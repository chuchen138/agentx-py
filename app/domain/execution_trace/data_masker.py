import re


class DataMasker:
    MASK_PATTERNS = {
        'phone': (r'1[3-9]\d{9}', lambda m: m.group()[:3] + '****' + m.group()[-4:]),
        'email': (r'[\w.-]+@[\w.-]+', lambda m: m.group().split('@')[0][:3] + '***@' + m.group().split('@')[1]),
        'id_card': (r'[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]', 
                   lambda m: m.group()[:3] + '********' + m.group()[-3:]),
        'bank_card': (r'\d{16,19}', lambda m: '**** **** **** ' + m.group()[-4:]),
        'token': (r'\b(token|apikey|secret|password|key|auth)\b.*', lambda m: '***'),
    }
    
    @classmethod
    def mask(cls, data: str) -> str:
        """对数据进行脱敏处理"""
        if not isinstance(data, str):
            return data
        
        masked_data = data
        for pattern, replacer in cls.MASK_PATTERNS.values():
            masked_data = re.sub(pattern, replacer, masked_data, flags=re.IGNORECASE)
        return masked_data
    
    @classmethod
    def mask_dict(cls, data: dict) -> dict:
        """对字典中的数据进行脱敏处理"""
        if not isinstance(data, dict):
            return data
        
        masked_dict = {}
        for key, value in data.items():
            if isinstance(value, str):
                masked_dict[key] = cls.mask(value)
            elif isinstance(value, dict):
                masked_dict[key] = cls.mask_dict(value)
            elif isinstance(value, list):
                masked_dict[key] = [cls.mask_dict(item) if isinstance(item, dict) else cls.mask(item) if isinstance(item, str) else item for item in value]
            else:
                masked_dict[key] = value
        return masked_dict
