"""
Prompt templates for Mind Evolution v4 pipeline.
"""

PROBLEM_DESCRIPTION = """Planificar reuniones con 10 amigos en 2 dias (08:00-20:00 cada dia). Empiezas en Cafe Central cada dia.

PERSONAS, UBICACION, DIA, DISPONIBILIDAD Y DURACION:
DIA 1:
- Ana: Cafe Central, 09:00-12:00, 45min
- Bruno: Parque Norte, 10:00-13:00, 30min (PREREQUISITO: reunirse con Ana antes)
- Carla: Biblioteca Sur, 08:00-11:00, 60min
- Diego: Oficina Este, 14:00-17:00, 45min
- Elena: Centro Comercial, 15:00-19:00, 30min (puede ser dia 1 O dia 2)
- Felipe: Restaurante Oeste, 11:00-14:00, 60min

DIA 2:
- Gaby: Hotel Plaza, 09:00-12:00, 45min
- Hugo: Museo Central, 10:00-14:00, 30min (PREREQUISITO: reunirse con Gaby antes)
- Isabel: Parque Norte, 13:00-16:00, 60min
- Javier: Estacion Sur, 16:00-19:00, 45min (PREREQUISITO: reunirse con Isabel antes)

TIEMPOS DE VIAJE (minutos):
Cafe Central <-> Parque Norte: 20, Biblioteca Sur: 30, Oficina Este: 25, Centro Comercial: 35, Restaurante Oeste: 15, Hotel Plaza: 10, Museo Central: 20, Estacion Sur: 40
Parque Norte <-> Biblioteca Sur: 40, Oficina Este: 15, Centro Comercial: 25, Restaurante Oeste: 30, Hotel Plaza: 25, Museo Central: 15, Estacion Sur: 35
Biblioteca Sur <-> Oficina Este: 35, Centro Comercial: 45, Restaurante Oeste: 25, Hotel Plaza: 35, Museo Central: 30, Estacion Sur: 20
Oficina Este <-> Centro Comercial: 20, Restaurante Oeste: 30, Hotel Plaza: 30, Museo Central: 25, Estacion Sur: 35
Centro Comercial <-> Restaurante Oeste: 40, Hotel Plaza: 30, Museo Central: 20, Estacion Sur: 25
Restaurante Oeste <-> Hotel Plaza: 20, Museo Central: 25, Estacion Sur: 30
Hotel Plaza <-> Museo Central: 15, Estacion Sur: 35
Museo Central <-> Estacion Sur: 30

11 RESTRICCIONES:
C1: Cada reunion dentro de ventana de disponibilidad
C2: Respetar tiempo de viaje entre reuniones consecutivas
C3: No reuniones solapadas (por dia)
C4: Duracion minima respetada
C5: Horario 08:00-20:00
C6: Reunirse con al menos 7 de 10 personas
C7: Cada persona en su dia correcto (Elena puede ser cualquier dia)
C8: Empezar en Cafe Central cada dia
C9: Prerequisites: Bruno DESPUES de Ana, Hugo DESPUES de Gaby, Javier DESPUES de Isabel
C10: No repetir persona
C11: Minimo 4 reuniones dia 1 Y minimo 3 reuniones dia 2"""

JSON_FORMAT = '{"meetings": [{"person": "X", "day": 1, "start": "HH:MM", "end": "HH:MM"}, ...]}'

INIT_PROMPT = f"""Eres un planificador experto. Genera un plan de reuniones de 2 dias.

{PROBLEM_DESCRIPTION}

IMPORTANTE:
- Calcula tiempos de viaje EXACTOS entre ubicaciones consecutivas
- Verifica que cada reunion empiece DESPUES de llegar (fin anterior + viaje)
- Respeta prerrequisitos: Bruno despues de Ana, Hugo despues de Gaby, Javier despues de Isabel
- NO incluyas comentarios en el JSON

Responde SOLO con JSON valido, sin comentarios.
Formato: {JSON_FORMAT}"""

CRITIC_PROMPT = f"""Eres un auditor de planes de reuniones de 2 dias.

{PROBLEM_DESCRIPTION}

PLAN A EVALUAR:
<<solution>>

VIOLACIONES DETECTADAS:
<<feedback>>

Analiza las violaciones. Para CADA una indica el cambio exacto: que persona mover, a que hora, teniendo en cuenta el tiempo de viaje. Max 6 bullet points.
NO incluyas JSON."""

AUTHOR_PROMPT = f"""Eres un planificador que corrige planes de reuniones de 2 dias.

{PROBLEM_DESCRIPTION}

PLAN ANTERIOR:
<<solution>>

CAMBIOS NECESARIOS:
<<critique>>

Aplica TODOS los cambios. Recalcula tiempos de viaje. Verifica prerrequisitos.
Responde SOLO con JSON valido corregido.
Formato: {JSON_FORMAT}"""

CROSSOVER_PROMPT = f"""Eres un optimizador de planes de reuniones de 2 dias.

{PROBLEM_DESCRIPTION}

Combina los mejores aspectos de dos planes. Toma reuniones sin violaciones de cada padre.

PADRE A (score <<score_a>>):
<<parent_a>>

PADRE B (score <<score_b>>):
<<parent_b>>

Recalcula tiempos de viaje para el plan combinado. Verifica prerrequisitos.
Responde SOLO con JSON valido.
Formato: {JSON_FORMAT}"""
