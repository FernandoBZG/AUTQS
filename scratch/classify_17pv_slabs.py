import sys, os, re

# Complete analysis script for 17PV slabs loading

# Slabs extracted from 17PV.LST and LAJ0291.DWG
# Coordinates are in cm
slabs = {
    'L4': {'area': 6.13, 'pos': (16473.0, -2732.4), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Leste'},
    'L5': {'area': 2.82, 'pos': (10597.8, -2707.9), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Oeste'},
    'L6': {'area': 6.13, 'pos': (10427.0, -2732.4), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Oeste'},
    'L8': {'area': 3.04, 'pos': (16298.0, -2702.4), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Leste'},
    'L9': {'area': 7.52, 'pos': (11482.0, -2737.4), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro-Oeste'},
    'L10': {'area': 8.21, 'pos': (10787.0, -2757.4), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Oeste'},
    'L11': {'area': 7.52, 'pos': (15413.0, -2737.4), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro-Leste'},
    'L12': {'area': 13.30, 'pos': (14019.8, -2790.5), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro-Leste'},
    'L13': {'area': 20.16, 'pos': (11872.4, -2799.1), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro-Oeste'},
    'L14': {'area': 13.30, 'pos': (12623.7, -2790.6), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro-Oeste'},
    'L15': {'area': 13.30, 'pos': (13015.2, -2790.6), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro-Oeste'},
    'L16': {'area': 13.30, 'pos': (15089.8, -2790.6), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro-Leste'},
    'L17': {'area': 8.21, 'pos': (16103.0, -2757.4), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Leste'},
    'L18': {'area': 13.19, 'pos': (14410.2, -2788.4), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro-Leste'},
    'L19': {'area': 14.09, 'pos': (13709.2, -2802.8), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro'},
    'L20': {'area': 23.23, 'pos': (10304.5, -2920.2), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Oeste'},
    'L21': {'area': 21.03, 'pos': (11133.3, -2827.3), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Oeste'},
    'L22': {'area': 23.23, 'pos': (16585.5, -2920.2), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Leste'},
    'L23': {'area': 3.29, 'pos': (11487.0, -2954.9), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro-Oeste'},
    'L24': {'area': 3.15, 'pos': (12907.0, -2969.9), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro-Oeste'},
    'L25': {'area': 14.09, 'pos': (13325.7, -2802.8), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro'},
    'L26': {'area': 21.03, 'pos': (15756.7, -2827.3), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Leste'},
    'L27': {'area': 3.15, 'pos': (12732.0, -2969.9), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro-Oeste'},
    'L28': {'area': 2.92, 'pos': (11724.2, -2996.0), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro-Oeste'},
    'L29': {'area': 3.15, 'pos': (14128.0, -2969.9), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro-Leste'},
    'L30': {'area': 3.15, 'pos': (15198.0, -2969.9), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro-Leste'},
    'L31': {'area': 3.15, 'pos': (14303.0, -2969.9), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro-Leste'},
    'L32': {'area': 3.29, 'pos': (15403.0, -2954.9), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro-Leste'},
    'L33': {'area': 3.11, 'pos': (10781.8, -2988.8), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Oeste'},
    'L34': {'area': 3.04, 'pos': (13593.0, -3032.4), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro'},
    'L35': {'area': 3.31, 'pos': (16103.0, -2992.4), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Leste'},
    'L36': {'area': 3.04, 'pos': (13442.0, -3032.4), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro'},
    'L37': {'area': 54.26, 'pos': (14991.7, -3102.3), 'cdist_cur': 0.350, 'h': 16, 'zone': 'Centro-Leste'},
    'L38': {'area': 58.75, 'pos': (11964.9, -3105.6), 'cdist_cur': 0.350, 'h': 16, 'zone': 'Centro-Oeste'},
    'L39': {'area': 3.10, 'pos': (11719.5, -3297.4), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro-Oeste'},
    'L40': {'area': 3.31, 'pos': (10787.0, -3297.4), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Oeste'},
    'L41': {'area': 3.15, 'pos': (14303.0, -3319.9), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro-Leste'},
    'L42': {'area': 3.31, 'pos': (16103.0, -3297.4), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Leste'},
    'L44': {'area': 3.29, 'pos': (11487.0, -3334.9), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro-Oeste'},
    'L45': {'area': 3.15, 'pos': (12732.0, -3319.9), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro-Oeste'},
    'L46': {'area': 3.15, 'pos': (15198.0, -3319.8), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro-Leste'},
    'L47': {'area': 21.07, 'pos': (16534.6, -3386.3), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Leste'},
    'L48': {'area': 21.07, 'pos': (10355.4, -3386.3), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Oeste'},
    'L49': {'area': 3.09, 'pos': (15408.0, -3338.7), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro-Leste'},
    'L50': {'area': 21.03, 'pos': (15756.7, -3462.4), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Leste'},
    'L51': {'area': 8.13, 'pos': (12284.5, -3424.9), 'cdist_cur': 0.350, 'h': 16, 'zone': 'Centro-Oeste'},
    'L52': {'area': 8.13, 'pos': (14750.5, -3424.9), 'cdist_cur': 0.350, 'h': 16, 'zone': 'Centro-Leste'},
    'L54': {'area': 13.30, 'pos': (14411.3, -3499.2), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro-Leste'},
    'L55': {'area': 7.52, 'pos': (15413.0, -3552.4), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro-Leste'},
    'L56': {'area': 20.16, 'pos': (11872.4, -3490.7), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro-Oeste'},
    'L57': {'area': 13.30, 'pos': (12623.7, -3499.2), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro-Oeste'},
    'L60': {'area': 8.21, 'pos': (10787.0, -3532.4), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Oeste'},
    'L62': {'area': 13.30, 'pos': (15089.8, -3499.2), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro-Leste'},
    'L63': {'area': 8.21, 'pos': (16103.0, -3532.4), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Leste'},
    'L64': {'area': 6.60, 'pos': (10527.0, -3579.9), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Oeste'},
    'L65': {'area': 7.52, 'pos': (11477.0, -3552.4), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Centro-Oeste'},
    'L67': {'area': 21.03, 'pos': (11133.3, -3462.4), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Oeste'},
    'L68': {'area': 6.60, 'pos': (16363.0, -3579.9), 'cdist_cur': 0.200, 'h': 16, 'zone': 'Leste'},
    'L69': {'area': 44.19, 'pos': (13860.6, -3528.8), 'cdist_cur': 0.500, 'h': 16, 'zone': 'Centro-Leste'},
    'L70': {'area': 20.78, 'pos': (10889.1, -3686.1), 'cdist_cur': 0.500, 'h': 16, 'zone': 'Oeste'},
    'L71': {'area': 44.19, 'pos': (13174.4, -3528.8), 'cdist_cur': 0.500, 'h': 16, 'zone': 'Centro-Oeste'},
    'L72': {'area': 4.11, 'pos': (16787.7, -3463.6), 'cdist_cur': 0.500, 'h': 16, 'zone': 'Leste'},
}

# Detailed Architectural Space Mapping and Load Assignment:
# Space types:
# 1. PISCINA_ADULTO: L20 (main basin), part of L6
#    Delta_g = 14.5 kN/m2 (water 1.20m = 12.0 + tank finish/regularization 2.5)
#    q = 2.0 kN/m2 -> CDist = 1.65 tf/m2 (16.5 kN/m2)
#
# 2. PISCINA_INFANTIL_PRAINHA: L6, L5
#    Delta_g = 6.0 kN/m2 (water 0.35m = 3.5 + tank finish/regularization 2.5)
#    q = 2.0 kN/m2 -> CDist = 0.80 tf/m2 (8.0 kN/m2)
#
# 3. HIDRO_CASCATA: L14, L27
#    Delta_g = 11.0 kN/m2 (water 0.85m = 8.5 + tank finish 2.5)
#    q = 2.0 kN/m2 -> CDist = 1.30 tf/m2 (13.0 kN/m2)
#
# 4. DECK_SOLARIUM_ELEVADO: L10, L33, L48, L40, L60, L64, L70, L15, L24, L25
#    Delta_g = 2.5 kN/m2 (deck elevado/pedestais/regularizacao/impermeabilizacao)
#    q = 3.0 kN/m2 (recreacao/lazer uso comum NBR 6120) -> CDist = 0.55 tf/m2 (5.5 kN/m2)
#
# 5. TERRACO_DESCOBERTO_GOURMET_FIREPLACE: L4, L8, L17, L22, L26, L35, L42, L47, L50, L63, L68, L72, L56, L67, L69, L71
#    Delta_g = 3.0 kN/m2 (contrapiso caimento + impermeabilizacao dupla + argamassa + porcelanato + muretas/floreiras)
#    q = 3.0 kN/m2 (terraco comum/festas/gourmet NBR 6120) -> CDist = 0.60 tf/m2 (6.0 kN/m2)
#
# 6. COBERTO_LOUNGE_COWORKING_CIRC: L9, L13, L21, L23, L28, L36, L38, L39, L44, L65, L34, L19
#    Delta_g = 2.0 kN/m2 (contrapiso + porcelanato + forro gesso + alvenarias leves)
#    q = 3.0 kN/m2 (lounge/reuniao coletivo) -> CDist = 0.50 tf/m2 (5.0 kN/m2)
#
# 7. COBERTO_FITNESS: L11, L16, L30, L32, L46, L49, L55, L62
#    Delta_g = 2.5 kN/m2 (piso emborrachado/vinilico de alto impacto + contrapiso + forro)
#    q = 3.5 kN/m2 (academia/ginastica NBR 6120) -> CDist = 0.60 tf/m2 (6.0 kN/m2)
#
# 8. COBERTO_KIDS_MARKET: L12, L18, L29, L31, L37 (parte de L37)
#    Delta_g = 2.0 kN/m2
#    q = 2.5 kN/m2 -> CDist = 0.45 tf/m2 (4.5 kN/m2)
#
# 9. ESCADAS_DUTOS_WCS_DEPOSITOS: L51, L52, L41, L45, L54, L57
#    L51, L52 (Escadas pressurizadas): Delta_g = 1.5 kN/m2, q = 3.0 kN/m2 -> CDist = 0.45 tf/m2
#    L41, L45, L54, L57 (WCs e depositos): Delta_g = 2.0 kN/m2, q = 2.5 kN/m2 -> CDist = 0.45 tf/m2

def classify_slab(lid, s):
    x, y = s['pos']
    
    # Specific specialized assignments
    if lid == 'L20':
        return ('Piscina Adulto (Tanque Principal)', 'Piscina / Tanque d\'água', 14.5, 2.0, 1.65, 'ALERTA: Carga muito alta; verificar cisalhamento/punção e reforço de espessura')
    elif lid == 'L6':
        return ('Piscina Infantil / Transição Prainha', 'Piscina Infantil', 6.0, 2.0, 0.80, 'Lâmina d\'água rasa (prof ~ 35 cm) + tanque')
    elif lid == 'L5':
        return ('Prainha / Acesso Infantil', 'Prainha', 5.5, 2.0, 0.75, 'Lâmina d\'água de espelho (prof ~ 25-30 cm)')
    elif lid in ['L14']:
        return ('Cascata & Deck Hidromassagem', 'Hidromassagem / Água', 11.0, 2.0, 1.30, 'Tanque de SPA/Hidro com água (prof ~ 85 cm)')
    elif lid in ['L27']:
        return ('Hidromassagem / SPA', 'Hidromassagem / Água', 11.0, 2.0, 1.30, 'Tanque de SPA/Hidro com água (prof ~ 85 cm)')
    elif lid in ['L10', 'L33', 'L48', 'L40', 'L60', 'L64', 'L70']:
        return ('Deck Solarium (Piscina Oeste)', 'Deck Solarium Elevado', 2.5, 3.0, 0.55, 'Piso elevado/deck solarium sobre pedestais')
    elif lid in ['L15', 'L24', 'L25']:
        return ('Deck / Yoga / Meditação / Estar Norte', 'Deck Elevado Madeira', 2.5, 3.0, 0.55, 'Deck suspenso para ioga e contemplação')
    elif lid in ['L51', 'L52']:
        return ('Escada Pressurizada / Duto de Fumaça', 'Caixa de Escada Coletiva', 1.5, 3.0, 0.45, 'Escada enclausurada NBR 9077 / NBR 6120')
    elif lid in ['L41', 'L45', 'L54', 'L57']:
        return ('Sanitários Coletivos / PCD / Depósitos', 'Instalações Sanitárias / Apoio', 2.0, 2.5, 0.45, 'WCs de uso comum e depósito de manutenção')
    elif lid in ['L11', 'L16', 'L30', 'L32', 'L46', 'L49', 'L55', 'L62']:
        return ('Academia Fitness / Relax Fitness', 'Fitness / Musculação', 2.5, 3.5, 0.60, 'Área fitness com aparelhos e pesos')
    elif lid in ['L12', 'L18', 'L29', 'L31']:
        return ('Espaço Kids / Brinquedoteca', 'Área de Recreação Infantil', 2.0, 2.5, 0.45, 'Ambiente infantil coberto')
    elif lid == 'L37':
        return ('Hall Central Leste / Market Place / Circ.', 'Hall / Circulação Coletiva', 2.0, 3.0, 0.50, 'Circulação principal de acesso aos elevadores Leste')
    elif lid == 'L38':
        return ('Hall Central Oeste / Rooftop Lounge', 'Lounge Coberto / Convivência', 2.0, 3.0, 0.50, 'Lounge e circulação dos elevadores Oeste')
    elif lid in ['L9', 'L13', 'L21', 'L23', 'L28', 'L34', 'L36', 'L39', 'L44', 'L65', 'L19']:
        return ('Rooftop Lounge Coberto / Pooltable / Circ.', 'Lounge Social Coberto', 2.0, 3.0, 0.50, 'Espaço de convivência social e jogos')
    elif lid in ['L42', 'L47', 'L50', 'L63', 'L68']:
        return ('Gazebo Gourmet / Churrasqueira / Fireplace', 'Área Gourmet / Festas Externa', 3.0, 3.0, 0.60, 'Bancadas, churrasqueira, fogo de chão, impermeabilização')
    elif lid in ['L4', 'L8', 'L17', 'L22', 'L26', 'L35', 'L72']:
        return ('Estar Contemplativo Leste / Sacada Externa', 'Terraço Descoberto Panorâmico', 2.8, 3.0, 0.58, 'Piso externo impermeabilizado com guarda-corpos')
    elif lid in ['L56', 'L67']:
        return ('Lareira Ecológica Oeste / Solarium Sul', 'Terraço de Convivência Descoberto', 2.8, 3.0, 0.58, 'Lareiras externas, bancos e impermeabilização')
    elif lid in ['L69', 'L71']:
        return ('Espaço Terraço / Coworking Sky / Contemplation', 'Terraço / Coworking de Uso Misto', 2.5, 3.0, 0.55, 'Área mista aberta com coworking panorâmico')
    else:
        return ('Terraço Rooftop / Convivência', 'Uso Comum Geral', 2.5, 3.0, 0.55, 'Padrão NBR 6120')

results = []
for lid in sorted(slabs.keys(), key=lambda x: int(x[1:])):
    s = slabs[lid]
    amb, cat, dg, q, cdist, obs = classify_slab(lid, s)
    results.append({
        'lid': lid,
        'area': s['area'],
        'cur_cdist': s['cdist_cur'],
        'amb': amb,
        'cat': cat,
        'dg_kn': dg,
        'q_kn': q,
        'cdist_tf': cdist,
        'cdist_kn': cdist * 10.0,
        'obs': obs
    })

print(f"{'Laje':<5} | {'Área (m2)':<9} | {'Ambiente / Uso no Rooftop':<40} | {'dg (kN/m2)':<10} | {'q (kN/m2)':<10} | {'CDist TQS (tf/m2)':<17} | {'Atual (tf/m2)':<13}")
print("-" * 115)
for r in results:
    print(f"{r['lid']:<5} | {r['area']:9.2f} | {r['amb']:<40} | {r['dg_kn']:10.2f} | {r['q_kn']:10.2f} | {r['cdist_tf']:17.3f} | {r['cur_cdist']:13.3f}")
