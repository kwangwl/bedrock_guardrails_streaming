import boto3


def apply_guardrail(text, text_type, region, guardrail_id, guardrail_version):
    """가드레일 적용"""
    try:
        bedrock_runtime = boto3.client("bedrock-runtime", region_name=region)

        # 가드레일 적용
        response = bedrock_runtime.apply_guardrail(
            guardrailIdentifier=guardrail_id,
            guardrailVersion=guardrail_version,
            source=text_type,       # 'INPUT' or 'OUTPUT'
            content=[{"text": {"text": text}}]
        )

        # 위반 사항 체크
        blocked_count, anonymized_count, masked_count, violations = _check_violations(response)

        if blocked_count > 0:
            filtered_text = response.get('outputs', [{}])[0].get('text', text)
            return "blocked", violations, filtered_text, response

        elif anonymized_count > 0:
            filtered_text = response.get('outputs', [{}])[0].get('text', text)
            return "anonymized", violations, filtered_text, response

        else:
            return "passed", [], text, response

    except Exception as e:
        print(f"가드레일 적용 중 오류 발생: {str(e)}")


def _check_violations(response):
    """가드레일 위반 사항 체크"""
    if response['action'] == 'GUARDRAIL_INTERVENED':
        violations = []

        # 주요 정책 위반 체크
        for assessment in response.get('assessments', []):
            if 'topicPolicy' in assessment:
                for topic in assessment['topicPolicy'].get('topics', []):
                    _add_violations(violations, "Word filters", topic['action'], topic['name'])

            if 'contentPolicy' in assessment:
                # 콘텐츠 관련 정책
                for filtered in assessment['contentPolicy'].get('filters', []):
                    _add_violations(violations, "Content filters", filtered['action'], filtered['type'])

            if 'sensitiveInformationPolicy' in assessment:
                # 민감 정보 정책 (PII 엔티티 및 정규식)
                for regex in assessment['sensitiveInformationPolicy'].get('regexes', []):
                    _add_violations(violations, "Regex filter", regex['action'], regex['name'])

                for pii in assessment['sensitiveInformationPolicy'].get('piiEntities', []):
                    _add_violations(violations, "pii filter", pii['action'], pii['type'])

            if 'wordPolicy' in assessment:
                # 단어 관련 정책 (사용자 정의 단어 및 관리되는 단어 목록)
                for word in assessment['wordPolicy'].get('customWords', []):
                    _add_violations(violations, "Custom word filters", word['action'], word['match'])

                for word in assessment['wordPolicy'].get('managedWordLists', []):
                    _add_violations(violations, "Managed word filters", word['action'], word['match'])

        # 위반(BLOCKED, MASKED) 개수 계산
        blocked_count = sum(1 for v in violations if v.get('Action') == 'BLOCKED')
        anonymized_count = sum(1 for v in violations if v.get('Action') == 'ANONYMIZED')
        masked_count = sum(1 for v in violations if v.get('Action') == 'MASKED')

        return blocked_count, anonymized_count, masked_count, violations

    return 0, 0, 0, []


def _add_violations(results, category, action, name):
    results.append({
        "Category": category,
        "Action": action,
        "Name": name
    })
