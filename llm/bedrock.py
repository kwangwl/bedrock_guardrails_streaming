import boto3


def get_streaming_response(prompt, model_id, region):
    """Bedrock LLM 스트리밍 응답 호출"""
    try:
        client = boto3.client("bedrock-runtime", region_name=region)
        response = client.converse_stream(
            modelId=model_id,
            messages=[{
                "role": "user",
                "content": [{"text": prompt}]
            }],
            inferenceConfig={
                "maxTokens": 3000,
                "temperature": 0.0
            }
        )
        return response

    except Exception as e:
        raise Exception(f"Bedrock API 호출 실패: {str(e)}")
