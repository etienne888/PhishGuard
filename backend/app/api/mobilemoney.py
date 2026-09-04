# backend/app/api/mobile_money.py

from flask import Blueprint, request, jsonify
from flask_login import login_required
import re

mobile_money_bp = Blueprint('mobile_money', __name__)

# Patterns for detection
CRITICAL_PATTERNS = [
    (r'code (pin|otp|sécurité)', 'NEVER share PIN/OTP'),
    (r'agent.*mobile.*money', 'Fake agent scam'),
    (r'donner.*votre.*téléphone', 'SIM swap attempt'),
    (r'éteindre.*téléphone', 'SIM swap attempt'),
    (r'momo.*kash', 'Fake MTN service'),
]

SUSPICIOUS_DOMAINS = [
    r'\.tk', r'\.ml', r'\.ga', r'\.cf',
    r'verify.*mtn', r'secure.*orange',
]

@mobile_money_bp.route('/analyze', methods=['POST'])
def analyze_mobile_message():
    """Analyze a mobile money message for fraud"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'Message text is required'}), 400
        
        result = {
            'is_suspicious': False,
            'risk_level': 'low',
            'indicators': [],
            'official_service': None,
            'user_guidance': {}
        }
        
        text_lower = text.lower()
        
        # Check for mobile money keywords
        mobile_keywords = ['momo', 'mobile money', 'mtn', 'orange money', 'camtel']
        if not any(kw in text_lower for kw in mobile_keywords):
            result['user_guidance'] = {
                'summary': 'This message does not appear to be related to mobile money',
                'action': 'No action needed',
                'steps': ['Continue with caution']
            }
            return jsonify(result), 200
        
        # Check for critical patterns
        indicators = []
        for pattern, description in CRITICAL_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                indicators.append({
                    'type': 'critical',
                    'description': description,
                    'severity': 'critical'
                })
        
        if indicators:
            result['is_suspicious'] = True
            result['risk_level'] = 'critical'
            result['indicators'] = indicators
            result['user_guidance'] = {
                'summary': '🚨 CRITICAL: This is a confirmed scam attempt!',
                'action': 'DO NOT respond to this message.',
                'official_contact': 'Call MTN: 150 | Orange: 160 | CIRT-CM: 8202',
                'steps': [
                    'Do not reply or call any numbers in the message',
                    'Do not share any codes or personal information',
                    'Contact your operator using the official number above',
                    'Report the scam to CIRT-CM at alerts@cirt.cm'
                ]
            }
            return jsonify(result), 200
        
        # Check for official services
        if any(code in text for code in ['*126#', '*126*']):
            result['official_service'] = 'MTN'
        elif any(code in text for code in ['*124#', '*144#']):
            result['official_service'] = 'Orange'
        
        # Check for suspicious elements
        suspicious_elements = []
        for domain in SUSPICIOUS_DOMAINS:
            if re.search(domain, text_lower, re.IGNORECASE):
                suspicious_elements.append({
                    'type': 'suspicious_link',
                    'description': f'Message contains suspicious link pattern: {domain}',
                    'severity': 'high'
                })
        
        if suspicious_elements:
            result['is_suspicious'] = True
            result['risk_level'] = 'medium'
            result['indicators'] = suspicious_elements
        
        # Generate guidance
        if result['risk_level'] == 'medium':
            result['user_guidance'] = {
                'summary': '🟠 MEDIUM RISK: This message has suspicious elements',
                'action': 'Verify using official channels',
                'official_contact': f"Contact {result.get('official_service', 'your operator')}",
                'steps': [
                    'This message may be legitimate but has suspicious elements',
                    'Check your balance via USSD to confirm any transactions',
                    'Do not click links without verifying the sender',
                    'Contact customer care if you are unsure'
                ]
            }
        else:
            result['user_guidance'] = {
                'summary': '✅ LOW RISK: This message appears legitimate',
                'action': 'Continue with caution',
                'steps': [
                    'The message appears to be from an official source',
                    'Always verify transactions by checking your balance',
                    'If you receive similar messages, report suspicious ones'
                ]
            }
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mobile_money_bp.route('/ussd-codes', methods=['GET'])
def get_ussd_codes():
    """Get USSD codes for verification"""
    return jsonify({
        'mtn': {
            'balance': '*126#',
            'transfer': '*126*1#',
            'customer_care': '150'
        },
        'orange': {
            'balance': '*124#',
            'transfer': '*144#',
            'customer_care': '160'
        },
        'camtel': {
            'customer_care': '188'
        }
    })