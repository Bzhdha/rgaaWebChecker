import yaml
import re

def extract_rgaa_criteria():
    # Structure des critères RGAA 4.1
    criteria = {
        'themes': [
            {
                'id': '1',
                'name': 'Images',
                'criteria': [
                    {
                        'id': '1.1',
                        'description': 'Chaque image porteuse d\'information a-t-elle une alternative textuelle ?',
                        'test': 'Chaque image porteuse d\'information a-t-elle une alternative textuelle ?',
                        'level': 'A'
                    },
                    {
                        'id': '1.2',
                        'description': 'Chaque image de décoration est-elle correctement ignorée par les technologies d\'assistance ?',
                        'test': 'Chaque image de décoration est-elle correctement ignorée par les technologies d\'assistance ?',
                        'level': 'A'
                    }
                ]
            },
            {
                'id': '2',
                'name': 'Cadres',
                'criteria': [
                    {
                        'id': '2.1',
                        'description': 'Chaque cadre a-t-il un titre de cadre ?',
                        'test': 'Chaque cadre a-t-il un titre de cadre ?',
                        'level': 'A'
                    }
                ]
            }
        ]
    }
    
    # Sauvegarder en YAML
    with open('rgaa_4_1_criteria.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(criteria, f, allow_unicode=True, sort_keys=False)

if __name__ == '__main__':
    extract_rgaa_criteria() 