"""
Safety Layer

Validates responses for safety violations:
- Medicine/drug name detection
- Diagnosis language detection
- Red flag symptom detection
- Dosage information validation
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class SafetyViolation:
    """Container for safety violation."""
    type: str  # 'medicine', 'diagnosis', 'dosage', 'red_flag'
    severity: str  # 'critical', 'high', 'medium', 'low'
    message: str
    location: str  # Where in response


class SafetyLayer:
    """
    Safety validation layer for responses.
    """
    
    def __init__(self):
        """Initialize safety layer with detection patterns."""
        
        # Medicine/drug name patterns (common ones)
        self.medicine_patterns = [
            # Pain relievers
            r'\b(ibuprofen|advil|motrin|tylenol|acetaminophen|aspirin|aleve|naproxen)\b',
            # Antibiotics
            r'\b(amoxicillin|penicillin|azithromycin|ciprofloxacin|doxycycline)\b',
            # Hormones
            r'\b(premarin|estrace|climara|vivelle|prempro|provera|prometrium)\b',
            # Antidepressants
            r'\b(prozac|zoloft|lexapro|paxil|effexor|cymbalta|wellbutrin)\b',
            # Sleep aids
            r'\b(ambien|lunesta|benadryl|unisom)\b',
            # Other common meds
            r'\b(gabapentin|clonidine|fezolinetant|veozah)\b',
        ]
        
        # Diagnosis language patterns
        self.diagnosis_patterns = [
            r'\byou have\b.*\b(disease|disorder|condition|syndrome)',
            r'\byou are diagnosed with\b',
            r'\bthis is\b.*\b(disease|disorder|condition)',
            r'\byou suffer from\b',
        ]
        
        # Red flag symptoms (comprehensive list for metadata logging)
        self.red_flag_keywords = [
            # Post-menopausal bleeding
            'post-menopausal bleeding',
            'bleeding after menopause',
            # Chest pain
            'severe chest pain',
            'chest pain',
            # Headache with red flags
            'severe headache',
            'worst headache',
            'vision changes',
            'blurred vision',
            # Breast concerns
            'new breast lump',
            'breast lump',
            # Mental health crisis
            'suicidal',
            'want to die',
            'kill myself',
            'severe depression',
            'self-harm',
            # Cognitive red flags
            'forgetting how to',
            'confusion',
            # Bleeding patterns
            'heavy bleeding',
            'bleeding a lot',
            'bleeding heavily',
            'excessive bleeding',
            'hemorrhage',
            'soaking through',
            # Severe pain patterns
            'severe pain',
            'extreme pain',
            'unbearable pain',
            'excruciating pain',
            # Weakness/neurological
            'sudden weakness',
            'numbness',
            'can\'t move',
        ]
        
        # Allowed supplements (these are OK to mention)
        self.allowed_supplements = [
            'vitamin d', 'vitamin c', 'vitamin e', 'vitamin b',
            'calcium', 'magnesium', 'iron', 'folic acid', 'folate',
            'omega-3', 'fish oil', 'probiotics', 'melatonin',
            'black cohosh', 'evening primrose', 'soy isoflavones',
        ]
    
    def check_response(self, response: str) -> Tuple[bool, List[SafetyViolation]]:
        """
        Check response for safety violations.
        
        Args:
            response: Generated response text
            
        Returns:
            Tuple of (is_safe, violations_list)
        """
        violations = []
        
        # Check for medicine names
        medicine_violations = self._check_medicines(response)
        violations.extend(medicine_violations)
        
        # Check for diagnosis language
        diagnosis_violations = self._check_diagnosis_language(response)
        violations.extend(diagnosis_violations)
        
        # Check for dosage information
        dosage_violations = self._check_dosages(response)
        violations.extend(dosage_violations)
        
        # Determine if safe
        is_safe = not any(v.severity in ['critical', 'high'] for v in violations)
        
        return is_safe, violations
    
    def _check_medicines(self, text: str) -> List[SafetyViolation]:
        """Check for medicine/drug names."""
        violations = []
        text_lower = text.lower()
        
        # Check if it's in allowed supplements context
        for supplement in self.allowed_supplements:
            if supplement in text_lower:
                # This is OK
                continue
        
        # Check for medicine patterns
        for pattern in self.medicine_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                medicine_name = match.group()
                
                # Check if it's in a disclaimer context
                context_start = max(0, match.start() - 100)
                context_end = min(len(text), match.end() + 100)
                context = text[context_start:context_end].lower()
                
                # If it's in a "don't take" or "avoid" context, it's OK
                if any(phrase in context for phrase in ['do not take', 'avoid', 'should not use']):
                    continue
                
                violations.append(SafetyViolation(
                    type='medicine',
                    severity='critical',
                    message=f'Mentioned medicine name: {medicine_name}',
                    location=f'Position {match.start()}-{match.end()}'
                ))
        
        return violations
    
    def _check_diagnosis_language(self, text: str) -> List[SafetyViolation]:
        """Check for diagnosis language."""
        violations = []
        
        for pattern in self.diagnosis_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                violations.append(SafetyViolation(
                    type='diagnosis',
                    severity='high',
                    message=f'Used diagnosis language: {match.group()}',
                    location=f'Position {match.start()}-{match.end()}'
                ))
        
        return violations
    
    def _check_dosages(self, text: str) -> List[SafetyViolation]:
        """Check for specific dosage information."""
        violations = []
        
        # Pattern for specific dosages (e.g., "take 500mg", "2 tablets")
        dosage_pattern = r'\b(take|use)\s+\d+\s*(mg|mcg|g|ml|tablets?|pills?|capsules?)\b'
        
        matches = re.finditer(dosage_pattern, text, re.IGNORECASE)
        for match in matches:
            # Check if it's in informational context
            context_start = max(0, match.start() - 50)
            context_end = min(len(text), match.end() + 50)
            context = text[context_start:context_end].lower()
            
            # If it says "typically" or "commonly" or "range", it's informational
            if any(word in context for word in ['typically', 'commonly', 'usually', 'range', 'general']):
                continue
            
            violations.append(SafetyViolation(
                type='dosage',
                severity='medium',
                message=f'Specific dosage mentioned: {match.group()}',
                location=f'Position {match.start()}-{match.end()}'
            ))
        
        return violations
    
    def detect_red_flags(self, user_message: str) -> List[str]:
        """
        Detect red flag symptoms in user message.
        
        Args:
            user_message: User's message
            
        Returns:
            List of detected red flags
        """
        detected = []
        message_lower = user_message.lower()
        
        for keyword in self.red_flag_keywords:
            if keyword in message_lower:
                detected.append(keyword)
        
        return detected
    
    def get_red_flag_response(self, red_flags: List[str]) -> str:
        """
        Get appropriate response for red flag symptoms.
        
        Args:
            red_flags: List of detected red flags
            
        Returns:
            Warning message
        """
        if not red_flags:
            return ""
        
        # Critical red flags requiring immediate attention
        critical_flags = [
            'post-menopausal bleeding', 'bleeding after menopause',
            'severe chest pain', 'chest pain',
            'suicidal', 'want to die'
        ]
        
        is_critical = any(flag in red_flags for flag in critical_flags)
        
        if is_critical:
            return (
                "⚠️ IMPORTANT: What you're describing requires urgent medical attention. "
                "Please contact your healthcare provider immediately, visit urgent care, "
                "or call emergency services if needed. While I can provide educational "
                "information, this symptom needs professional evaluation right away."
            )
        else:
            return (
                "⚠️ The symptom you mentioned should be evaluated by a healthcare provider. "
                "Please schedule an appointment to discuss this with your doctor. "
                "I can provide general information, but professional assessment is important."
            )
