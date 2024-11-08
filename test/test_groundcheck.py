import boto3


def test_grounding_cases(region, guardrail_id, guardrail_version):
    """테스트 케이스 실행"""

    # 테스트 케이스 정의
    test_cases = [
        {
            "category": "Grounded & Relevant",
            "english": {
                "ground_source": "London is the capital of the UK. Seoul is the capital of South Korea.",
                "query": "What is the capital of South Korea?",
                "content": "The capital of South Korea is Seoul.",
                "expected": "pass"
            },
            "korean": {
                "ground_source": "런던은 영국의 수도입니다. 서울은 한국의 수도입니다.",
                "query": "한국의 수도는 무엇인가요?",
                "content": "한국의 수도는 서울입니다.",
                "expected": "pass"
            }
        },
        {
            "category": "Ungrounded but Relevant",
            "english": {
                "ground_source": "London is the capital of the UK. Seoul is the capital of South Korea.",
                "query": "What is the capital of South Korea?",
                "content": "The capital of South Korea is London.",
                "expected": "fail"
            },
            "korean": {
                "ground_source": "런던은 영국의 수도입니다. 서울은 한국의 수도입니다.",
                "query": "한국의 수도는 무엇인가요?",
                "content": "한국의 수도는 런던입니다.",
                "expected": "fail"
            }
        },
        {
            "category": "Grounded but Irrelevant",
            "english": {
                "ground_source": "London is the capital of the UK. Seoul is the capital of South Korea.",
                "query": "What is the capital of South Korea?",
                "content": "The capital of the UK is London.",
                "expected": "partial"
            },
            "korean": {
                "ground_source": "런던은 영국의 수도입니다. 서울은 한국의 수도입니다.",
                "query": "한국의 수도는 무엇인가요?",
                "content": "영국의 수도는 런던입니다.",
                "expected": "partial"
            }
        },
        {
            "category": "Ungrounded & Irrelevant",
            "english": {
                "ground_source": "London is the capital of the UK. Seoul is the capital of South Korea.",
                "query": "What is the capital of South Korea?",
                "content": "Tokyo is the capital of Japan.",
                "expected": "fail"
            },
            "korean": {
                "ground_source": "런던은 영국의 수도입니다. 서울은 한국의 수도입니다.",
                "query": "한국의 수도는 무엇인가요?",
                "content": "도쿄는 일본의 수도입니다.",
                "expected": "fail"
            }
        }
    ]

    results = []

    for test_case in test_cases:
        print(f"\n테스트 케이스: {test_case['category']}")

        # 영어 테스트
        print("\nEnglish Test:")
        en_status, en_violations, en_filtered, en_response = apply_guardrail(
            text=test_case['english'],
            text_type="OUTPUT",
            region=region,
            guardrail_id=guardrail_id,
            guardrail_version=guardrail_version
        )

        # 한글 테스트
        print("\n한글 테스트:")
        kr_status, kr_violations, kr_filtered, kr_response = apply_guardrail(
            text=test_case['korean'],
            text_type="OUTPUT",
            region=region,
            guardrail_id=guardrail_id,
            guardrail_version=guardrail_version
        )

        result = {
            "category": test_case['category'],
            "english_result": {
                "expected": test_case['english']['expected'],
                "actual_status": en_status,
                "violations": en_violations,
                "filtered_text": en_filtered
            },
            "korean_result": {
                "expected": test_case['korean']['expected'],
                "actual_status": kr_status,
                "violations": kr_violations,
                "filtered_text": kr_filtered
            }
        }

        results.append(result)

        # 결과 출력
        print(f"\n결과 - {test_case['category']}:")
        print(f"영어 테스트 - 예상: {test_case['english']['expected']}, 실제: {en_status}")
        print(f"한글 테스트 - 예상: {test_case['korean']['expected']}, 실제: {kr_status}")
        if en_violations:
            print("영어 위반사항:", en_violations)
        if kr_violations:
            print("한글 위반사항:", kr_violations)

    return results


def apply_guardrail(text, text_type, region, guardrail_id, guardrail_version):
    """가드레일 적용 및 결과 분석"""
    try:
        input_data = [
            {
                "text": {
                    "text": text["ground_source"],
                    "qualifiers": ["grounding_source"]
                }
            },
            {
                "text": {
                    "text": text["query"],
                    "qualifiers": ["query"]
                }
            },
            {
                "text": {
                    "text": text["content"]
                }
            }
        ]

        client = boto3.client("bedrock-runtime", region_name=region)
        response = client.apply_guardrail(
            guardrailIdentifier=guardrail_id,
            guardrailVersion=guardrail_version,
            source=text_type,
            content=input_data
        )

        # 가드레일 위반 체크
        violations = []
        if response['action'] == 'GUARDRAIL_INTERVENED':
            for assessment in response.get('assessments', []):
                _check_violations(assessment, violations)

        # 필터링된 텍스트
        outputs = response.get('outputs', [])
        filtered_text = outputs[0].get('text', text) if outputs else text

        # 상태 결정
        if any(v['Action'] == 'BLOCKED' for v in violations):
            return "blocked", violations, filtered_text, response
        elif any(v['Action'] == 'ANONYMIZED' for v in violations):
            return "anonymized", violations, filtered_text, response
        else:
            return "passed", [], text, response

    except Exception as e:
        raise Exception(f"가드레일 적용 실패: {str(e)}")


def _check_violations(assessment, violations):
    """가드레일 위반 사항 체크"""
    # 토픽 정책
    if 'topicPolicy' in assessment:
        for topic in assessment['topicPolicy'].get('topics', []):
            violations.append({
                "Category": "Word filters",
                "Action": topic['action'],
                "Name": topic['name']
            })

    # 콘텐츠 정책
    if 'contentPolicy' in assessment:
        for filtered in assessment['contentPolicy'].get('filters', []):
            violations.append({
                "Category": "Content filters",
                "Action": filtered['action'],
                "Name": filtered['type']
            })

    # 민감 정보 정책
    if 'sensitiveInformationPolicy' in assessment:
        for regex in assessment['sensitiveInformationPolicy'].get('regexes', []):
            violations.append({
                "Category": "Regex filter",
                "Action": regex['action'],
                "Name": regex['name']
            })
        for pii in assessment['sensitiveInformationPolicy'].get('piiEntities', []):
            violations.append({
                "Category": "PII filter",
                "Action": pii['action'],
                "Name": pii['type']
            })

    # 단어 정책
    if 'wordPolicy' in assessment:
        for word in assessment['wordPolicy'].get('customWords', []):
            violations.append({
                "Category": "Custom word filters",
                "Action": word['action'],
                "Name": word['match']
            })
        for word in assessment['wordPolicy'].get('managedWordLists', []):
            violations.append({
                "Category": "Managed word filters",
                "Action": word['action'],
                "Name": word['match']
            })


if __name__ == "__main__":
    REGION = ""  # 사용할 리전
    GUARDRAIL_ID = ""
    GUARDRAIL_VERSION = ""  # 가드레일 버전

    results = test_grounding_cases(REGION, GUARDRAIL_ID, GUARDRAIL_VERSION)