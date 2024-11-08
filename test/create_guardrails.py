import boto3
import csv
from typing import List


def load_test_words(file_path: str) -> List[dict]:
    """CSV 파일에서 테스트 단어 로드"""
    words = []
    try:
        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # 헤더 스킵
            for row in reader:
                words.append({'text': row[0]})
    except Exception as e:
        print(f"Error loading test words: {e}")
    return words


def create_guardrails(name, region, file_path):
    client = boto3.client("bedrock", region_name=region)

    # CSV 파일에서 단어 로드
    custom_words = load_test_words(file_path)

    create_response = client.create_guardrail(
        name=name,
        description='Comprehensive content safety guardrail with custom words and topics.',
        topicPolicyConfig={
            'topicsConfig': [
                {
                    'name': 'Illegal Gambling',
                    'definition': 'Content promoting or discussing illegal gambling activities, betting, or casino operations.',
                    'type': 'DENY'
                },
                {
                    'name': 'Drug Trafficking',
                    'definition': 'Content related to illegal drug trade, distribution, or manufacturing.',
                    'type': 'DENY'
                },
                {
                    'name': 'Weapons Trading',
                    'definition': 'Content about illegal weapons trade, manufacturing, or distribution.',
                    'type': 'DENY'
                },
                {
                    'name': 'Adult Content',
                    'definition': 'Explicit adult content or pornographic material.',
                    'type': 'DENY'
                },
                {
                    'name': 'Hate Speech',
                    'definition': 'Content promoting discrimination or hatred against protected groups.',
                    'type': 'DENY'
                },
                {
                    'name': 'Violence',
                    'definition': 'Extreme violence, gore, or cruel content.',
                    'type': 'DENY'
                },
                {
                    'name': 'Terrorism',
                    'definition': 'Content promoting terrorism or extremist activities.',
                    'type': 'DENY'
                },
                {
                    'name': 'Human Trafficking',
                    'definition': 'Content related to human trafficking or exploitation.',
                    'type': 'DENY'
                },
                {
                    'name': 'Cybercrime',
                    'definition': 'Content about hacking, malware, or cyber attacks.',
                    'type': 'DENY'
                },
                {
                    'name': 'Financial Fraud',
                    'definition': 'Content promoting scams or financial fraud schemes.',
                    'type': 'DENY'
                },
                {
                    'name': 'Child Exploitation',
                    'definition': 'Content related to child abuse or exploitation.',
                    'type': 'DENY'
                },
                {
                    'name': 'Counterfeit Products',
                    'definition': 'Content about counterfeit goods or services.',
                    'type': 'DENY'
                },
                {
                    'name': 'Identity Theft',
                    'definition': 'Content about stealing or misusing personal identities.',
                    'type': 'DENY'
                },
                {
                    'name': 'Animal Cruelty',
                    'definition': 'Content showing or promoting animal abuse.',
                    'type': 'DENY'
                },
                {
                    'name': 'Illegal Substances',
                    'definition': 'Content about illegal drugs or controlled substances.',
                    'type': 'DENY'
                },
                {
                    'name': 'Harassment',
                    'definition': 'Content promoting bullying or harassment.',
                    'type': 'DENY'
                },
                {
                    'name': 'Extremist Content',
                    'definition': 'Content promoting extremist ideologies.',
                    'type': 'DENY'
                },
                {
                    'name': 'Illegal Hacking',
                    'definition': 'Content about unauthorized system access.',
                    'type': 'DENY'
                },
                {
                    'name': 'Privacy Violation',
                    'definition': 'Content violating personal privacy.',
                    'type': 'DENY'
                },
                {
                    'name': 'Black Market',
                    'definition': 'Content about illegal trading or black market activities.',
                    'type': 'DENY'
                },
                {
                    'name': 'Misinformation',
                    'definition': 'Deliberately false or misleading information.',
                    'type': 'DENY'
                },
                {
                    'name': 'Illegal Surveillance',
                    'definition': 'Content about unauthorized surveillance or spying.',
                    'type': 'DENY'
                },
                {
                    'name': 'Election Interference',
                    'definition': 'Content about manipulating election processes.',
                    'type': 'DENY'
                },
                {
                    'name': 'Illegal Immigration',
                    'definition': 'Content promoting illegal border crossing.',
                    'type': 'DENY'
                },
                {
                    'name': 'Copyright Violation',
                    'definition': 'Content violating intellectual property rights.',
                    'type': 'DENY'
                },
                {
                    'name': 'Market Manipulation',
                    'definition': 'Content about stock or market manipulation.',
                    'type': 'DENY'
                },
                {
                    'name': 'Unauthorized Practice',
                    'definition': 'Content about practicing without proper licenses.',
                    'type': 'DENY'
                },
                {
                    'name': 'Dangerous Challenges',
                    'definition': 'Content promoting harmful or dangerous activities.',
                    'type': 'DENY'
                },
                {
                    'name': 'Personal Data Theft',
                    'definition': 'Content about stealing personal information.',
                    'type': 'DENY'
                },
                {
                    'name': 'Revenge Content',
                    'definition': 'Content shared without consent for revenge.',
                    'type': 'DENY'
                }
            ]
        },
        contentPolicyConfig={
            'filtersConfig': [
                {
                    'type': 'SEXUAL',
                    'inputStrength': 'HIGH',
                    'outputStrength': 'HIGH'
                },
                {
                    'type': 'VIOLENCE',
                    'inputStrength': 'HIGH',
                    'outputStrength': 'HIGH'
                },
                {
                    'type': 'HATE',
                    'inputStrength': 'HIGH',
                    'outputStrength': 'HIGH'
                },
                {
                    'type': 'INSULTS',
                    'inputStrength': 'HIGH',
                    'outputStrength': 'HIGH'
                },
                {
                    'type': 'MISCONDUCT',
                    'inputStrength': 'HIGH',
                    'outputStrength': 'HIGH'
                },
                {
                    'type': 'PROMPT_ATTACK',
                    'inputStrength': 'HIGH',
                    'outputStrength': 'NONE'
                }
            ]
        },
        wordPolicyConfig={
            'wordsConfig': custom_words,  # CSV에서 로드한 단어들
            'managedWordListsConfig': [
                {'type': 'PROFANITY'}
            ]
        },
        sensitiveInformationPolicyConfig={
            'piiEntitiesConfig': [
                {'type': 'ADDRESS', 'action': 'ANONYMIZE'},
                {'type': 'AGE', 'action': 'ANONYMIZE'},
                {'type': 'AWS_ACCESS_KEY', 'action': 'ANONYMIZE'},
                {'type': 'AWS_SECRET_KEY', 'action': 'ANONYMIZE'},
                {'type': 'CA_HEALTH_NUMBER', 'action': 'ANONYMIZE'},
                {'type': 'CA_SOCIAL_INSURANCE_NUMBER', 'action': 'ANONYMIZE'},
                {'type': 'CREDIT_DEBIT_CARD_CVV', 'action': 'ANONYMIZE'},
                {'type': 'CREDIT_DEBIT_CARD_EXPIRY', 'action': 'ANONYMIZE'},
                {'type': 'CREDIT_DEBIT_CARD_NUMBER', 'action': 'ANONYMIZE'},
                {'type': 'DRIVER_ID', 'action': 'ANONYMIZE'},
                {'type': 'EMAIL', 'action': 'ANONYMIZE'},
                {'type': 'INTERNATIONAL_BANK_ACCOUNT_NUMBER', 'action': 'ANONYMIZE'},
                {'type': 'IP_ADDRESS', 'action': 'ANONYMIZE'},
                {'type': 'LICENSE_PLATE', 'action': 'ANONYMIZE'},
                {'type': 'MAC_ADDRESS', 'action': 'ANONYMIZE'},
                {'type': 'NAME', 'action': 'ANONYMIZE'},
                {'type': 'PASSWORD', 'action': 'ANONYMIZE'},
                {'type': 'PHONE', 'action': 'ANONYMIZE'},
                {'type': 'PIN', 'action': 'ANONYMIZE'},
                {'type': 'SWIFT_CODE', 'action': 'ANONYMIZE'},
                {'type': 'UK_NATIONAL_HEALTH_SERVICE_NUMBER', 'action': 'ANONYMIZE'},
                {'type': 'UK_NATIONAL_INSURANCE_NUMBER', 'action': 'ANONYMIZE'},
                {'type': 'UK_UNIQUE_TAXPAYER_REFERENCE_NUMBER', 'action': 'ANONYMIZE'},
                {'type': 'URL', 'action': 'ANONYMIZE'},
                {'type': 'USERNAME', 'action': 'ANONYMIZE'},
                {'type': 'US_BANK_ACCOUNT_NUMBER', 'action': 'ANONYMIZE'},
                {'type': 'US_BANK_ROUTING_NUMBER', 'action': 'ANONYMIZE'},
                {'type': 'US_INDIVIDUAL_TAX_IDENTIFICATION_NUMBER', 'action': 'ANONYMIZE'},
                {'type': 'US_PASSPORT_NUMBER', 'action': 'ANONYMIZE'},
                {'type': 'US_SOCIAL_SECURITY_NUMBER', 'action': 'ANONYMIZE'},
                {'type': 'VEHICLE_IDENTIFICATION_NUMBER', 'action': 'ANONYMIZE'}
            ],
            'regexesConfig': [
                {
                    'name': 'Credit Card Pattern',
                    'description': 'Matches credit card numbers in various formats',
                    'pattern': '\d{6}-\d{7}',
                    'action': 'ANONYMIZE'
                },
                {
                    'name': 'Email Pattern',
                    'description': 'Matches email addresses',
                    'pattern': '\d{5}-\d{7}',
                    'action': 'ANONYMIZE'
                },
                {
                    'name': 'Phone Number Pattern',
                    'description': 'Matches various phone number formats',
                    'pattern': '\d{4}-\d{7}',
                    'action': 'ANONYMIZE'
                },
                {
                    'name': 'SSN Pattern',
                    'description': 'Matches US Social Security Numbers',
                    'pattern': '\d{3}-\d{7}',
                    'action': 'ANONYMIZE'
                },
                {
                    'name': 'IP Address Pattern',
                    'description': 'Matches IPv4 addresses',
                    'pattern': '\d{2}-\d{7}',
                    'action': 'ANONYMIZE'
                },
                {
                    'name': 'Date Pattern',
                    'description': 'Matches dates in various formats',
                    'pattern': '\d{6}-\d{8}',
                    'action': 'ANONYMIZE'
                },
                {
                    'name': 'Password Pattern',
                    'description': 'Matches common password patterns',
                    'pattern': '\d{6}-\d{4}',
                    'action': 'ANONYMIZE'
                },
                {
                    'name': 'URL Pattern',
                    'description': 'Matches URLs',
                    'pattern': '\d{6}-\d{3}',
                    'action': 'ANONYMIZE'
                },
                {
                    'name': 'Bank Account Pattern',
                    'description': 'Matches bank account numbers',
                    'pattern': '\d{6}-\d{9}',
                    'action': 'ANONYMIZE'
                },
                {
                    'name': 'ZIP Code Pattern',
                    'description': 'Matches US ZIP codes',
                    'pattern': '\d{6}-\d{1}',
                    'action': 'ANONYMIZE'
                }
            ]
        },
        contextualGroundingPolicyConfig={
            'filtersConfig': [
                {
                    'type': 'GROUNDING',
                    'threshold': 0.75
                },
                {
                    'type': 'RELEVANCE',
                    'threshold': 0.75
                }
            ]
        },
        blockedInputMessaging="This content has been blocked due to violation of our content policies.",
        blockedOutputsMessaging="This response has been blocked due to violation of our content policies.",
        tags=[
            {'key': 'purpose', 'value': 'content-safety'},
            {'key': 'environment', 'value': 'production'}
        ]
    )

    print(create_response)


if __name__ == "__main__":
    create_guardrails("test11", "", "./test_words.csv")
