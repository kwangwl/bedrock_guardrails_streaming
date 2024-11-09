import time
import re
import random
import string
import boto3
from typing import List, Dict, Set
import csv
import os


def generate_test_content(length: int = 1000) -> str:
    """고정된 길이의 테스트 문장 생성"""
    words = ['안녕하세요', '테스트', '문장', '입니다', '생성된', '텍스트']
    result = []
    current_length = 0

    while current_length < length:
        word = random.choice(words)
        if current_length + len(word) + 1 <= length:  # +1 for space
            result.append(word)
            current_length += len(word) + 1
        else:
            break

    return ' '.join(result)


def generate_unique_word(used_words: Set[str], length: int) -> str:
    """중복되지 않는 단어 생성"""
    while True:
        word = ''.join(random.choices(string.ascii_lowercase, k=length))
        if word not in used_words:
            return word


def generate_test_words(count: int) -> List[str]:
    """중복되지 않는 테스트용 커스텀 단어 리스트 생성"""
    used_words = set()
    words = []

    for _ in range(count):
        # 5~10글자 길이의 랜덤 단어 생성
        word_length = random.randint(5, 10)
        word = generate_unique_word(used_words, word_length)
        words.append(word)
        used_words.add(word)

    return words


def save_test_words(words: List[str], file_path: str):
    """테스트 단어들을 CSV 파일로 저장"""
    with open(file_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['word'])  # 헤더
        for word in words:
            writer.writerow([word])


def load_test_words(file_path: str, count: int) -> List[str]:
    """CSV 파일에서 지정된 개수만큼의 테스트 단어 로드"""
    words = []
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # 헤더 스킵
        for row in reader:
            if len(words) >= count:
                break
            words.append(row[0])
    return words


def generate_unique_pattern(used_patterns: Set[str]) -> str:
    """중복되지 않는 정규식 패턴 생성"""
    while True:
        # 패턴 형식: test + 랜덤문자열 + [a-z]+
        random_part = ''.join(random.choices(string.ascii_lowercase, k=5))
        pattern = f"test{random_part}[a-z]+"
        if pattern not in used_patterns:
            return pattern


def generate_test_patterns(count: int) -> List[str]:
    """중복되지 않는 테스트용 정규식 패턴 리스트 생성"""
    used_patterns = set()
    patterns = []

    for _ in range(count):
        pattern = generate_unique_pattern(used_patterns)
        patterns.append(pattern)
        used_patterns.add(pattern)

    return patterns


class LocalGuardrail:
    def __init__(self, custom_words: List[str], regex_patterns: List[str]):
        self.custom_words = set(custom_words)  # 검색 최적화를 위해 set 사용
        self.regex_patterns = [re.compile(pattern) for pattern in regex_patterns]

    def check_content(self, text: str) -> Dict:
        start_time = time.time()

        # 커스텀 단어 체크
        word_matches = set()
        for word in self.custom_words:
            if word in text:
                word_matches.add(word)

        # 정규식 패턴 체크
        regex_matches = set()
        for pattern in self.regex_patterns:
            if pattern.search(text):
                regex_matches.add(pattern.pattern)

        end_time = time.time()

        return {
            "latency": end_time - start_time,
            "word_matches": len(word_matches),
            "regex_matches": len(regex_matches)
        }


class BedrockGuardrail:
    def __init__(self, region, guardrail_id, guardrail_version):
        self.client = boto3.client("bedrock-runtime", region_name=region)
        self.guardrail_id = guardrail_id
        self.guardrail_version = guardrail_version

    def check_content(self, text: str) -> Dict:
        start_time = time.time()

        try:
            response = self.client.apply_guardrail(
                guardrailIdentifier=self.guardrail_id,
                guardrailVersion=self.guardrail_version,
                source="OUTPUT",
                content=[
                    {
                        "text": {
                            "text": "London is the capital of the UK. Seoul is the capital of South Korea.",
                            "qualifiers": ["grounding_source"]
                        }
                    },
                    {
                        "text": {
                            "text": "What is the capital of South Korea?",
                            "qualifiers": ["query"]
                        }
                    },
                    {
                        "text": {
                            "text": "한국의 수도는 서울입니다."
                        }
                    }
                ]
            )

        except Exception as e:
            print(f"Error calling Bedrock: {e}")
            return {"latency": 0, "error": str(e)}

        end_time = time.time()
        latency = response['assessments'][0]['invocationMetrics']['guardrailProcessingLatency']
        return {
            "latency": latency,
            "response": response
        }


def run_performance_test(region, guardrail_id, guardrail_version, word_counts, iterations, words_file="./test_words.csv"):
    """다양한 단어 수에 대한 성능 테스트 실행"""
    results = {
        "local": {},
        "bedrock": {}
    }

    test_content = generate_test_content(1000)
    bedrock_guardrail = BedrockGuardrail(region, guardrail_id, guardrail_version)

    # 최대 단어 수만큼의 테스트 단어가 필요
    max_word_count = max(word_counts)

    # 파일이 없으면 생성
    if not os.path.exists(words_file):
        print(f"Generating {max_word_count} test words...")
        test_words = generate_test_words(max_word_count)
        save_test_words(test_words, words_file)
        print(f"Test words saved to {words_file}")

    for word_count in word_counts:
        print(f"\nTesting with {word_count} words...")

        # 파일에서 테스트 단어 로드
        test_words = load_test_words(words_file, word_count)
        test_patterns = generate_test_patterns(word_count)

        local_guardrail = LocalGuardrail(test_words, test_patterns)

        local_times = []
        bedrock_times = []

        for i in range(iterations):
            local_result = local_guardrail.check_content(test_content)
            local_times.append(local_result["latency"])

            bedrock_result = bedrock_guardrail.check_content(test_content)
            bedrock_times.append(bedrock_result["latency"])

        results["local"][word_count] = {
            "avg_time": sum(local_times) / len(local_times),
            "min_time": min(local_times),
            "max_time": max(local_times)
        }

        results["bedrock"][word_count] = {
            "avg_time": sum(bedrock_times) / len(bedrock_times),
            "min_time": min(bedrock_times),
            "max_time": max(bedrock_times)
        }

    return results


if __name__ == "__main__":
    word_counts = [1000]  # 테스트할 단어 개수

    results = run_performance_test(
        region="",
        guardrail_id="",
        guardrail_version="",
        word_counts=word_counts,
        iterations=5,
        words_file="test_words.csv"
    )

    # 결과 출력
    print("\nTest Results:")
    print("-" * 50)
    for word_count in word_counts:
        print(f"\nWord count: {word_count}")
        print("Local Guard Rail:")
        print(f"  Average: {results['local'][word_count]['avg_time']:.4f}s")
        print(f"  Min: {results['local'][word_count]['min_time']:.4f}s")
        print(f"  Max: {results['local'][word_count]['max_time']:.4f}s")

        print("Bedrock Guard Rail:")
        print(f"  Average: {results['bedrock'][word_count]['avg_time']:.4f}s")
        print(f"  Min: {results['bedrock'][word_count]['min_time']:.4f}s")
        print(f"  Max: {results['bedrock'][word_count]['max_time']:.4f}s")
