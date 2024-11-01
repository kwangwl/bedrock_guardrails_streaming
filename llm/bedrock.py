import boto3


def get_streaming_response(prompt, model_id, region):
    """llm streaming 응답 호출 (3rd party llm 변경 가능)"""
    try:
        bedrock_runtime = boto3.client("bedrock-runtime", region_name=region)

        message = {
            "role": "user",
            "content": [{"text": prompt}]
        }

        response = bedrock_runtime.converse_stream(
            modelId=model_id,
            messages=[message],
            inferenceConfig={
                "maxTokens": 3000,
                "temperature": 0.0
            }
        )

        return response

    except Exception as e:
        print(f"Bedrock API 호출 중 오류 발생: {str(e)}")
