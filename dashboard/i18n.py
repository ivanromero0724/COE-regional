"""English-first bilingual interface labels for the EOC-NET survey dashboard.

Only user-facing UI is translated. Source questionnaire replies are preserved
verbatim, so machine translation never alters a country's reported statements.
"""

ES = {
    # Site-wide / navigation
    'English':'Inglés','Español':'Español', 'Language / Idioma':'Idioma / Language',
    'EOC-NET / THE AMERICAS · 2026':'EOC-NET / LAS AMÉRICAS · 2026',
    'Health Emergency Operations Centres':'Centros de Operaciones de Emergencias en Salud',
    'Regional survey dashboard · Institutional preparedness, operational capacities and cooperation':
        'Tablero regional de la encuesta · Preparación institucional, capacidades operativas y cooperación',
    'REGIONAL MONITORING':'MONITOREO REGIONAL', 'REGIONAL SURVEY':'ENCUESTA REGIONAL',
    'EOC-S · Americas':'COE-S · Américas','PAHO/WHO survey 2026':'Encuesta OPS/OMS 2026',
    'Explore':'Explorar', 'Regional overview':'Panorama regional', 'Country profiles':'Perfiles por país',
    'Regional section':'Sección regional','Overview':'Panorama general',
    'Capacities & gaps':'Capacidades y brechas','Operations & hazards':'Operación y amenazas',
    'Networks & cooperation':'Redes y cooperación',
    'Geographic area':'Área geográfica','All regions':'Todas las subregiones',
    'Countries (optional)':'Países (opcional)',
    'Leave empty to include all countries in the selected area.':'Deje vacío para incluir todos los países del área seleccionada.',
    'South America':'América del Sur','Central America':'América Central','Caribbean':'Caribe',
    'countries':'países','institutional responses':'respuestas institucionales',
    'Source: local Excel in `data/` · Updated with GitHub redeploy':'Fuente: Excel en `data/` · Actualizado mediante despliegue de GitHub',
    'Select at least one country to display regional indicators.':'Seleccione al menos un país para mostrar los indicadores regionales.',
    # Main overview
    'Countries responding':'Países que respondieron','Established EOC-S':'COE-S establecidos',
    'In implementation':'En implementación', '24/7 operation':'Operación 24/7',
    'Activation under 2 h':'Activación en menos de 2 h',
    'Which countries have EOC-S?':'¿Qué países tienen COE-S?',
    'Established or in implementation; countries without survey responses remain gray.':'Establecidos o en implementación; los países sin respuesta se muestran en gris.',
    '01 / EOC-S STATUS':'01 / ESTADO DE LOS COE-S',
    'How the EOC-S operate':'¿Cómo operan los COE-S?',
    'One observation per responding country.':'Una observación por país que respondió.',
    '02 / OPERATIONS':'02 / OPERACIÓN','Operating mode':'Modalidad de operación',
    'Activation after formal decision':'Tiempo de activación tras la decisión formal',
    'Most widely reported capacities':'Capacidades más reportadas',
    'Countries reporting an established or functional capacity.':'Países con capacidades establecidas o funcionales.',
    '03 / REPORTED CAPACITIES':'03 / CAPACIDADES REPORTADAS',
    'Priority capacity gaps':'Brechas prioritarias de capacidad',
    'Countries with the following capacities fully in place.':'Países que cuentan plenamente con estas capacidades.',
    '04 / COOPERATION PRIORITIES':'04 / PRIORIDADES DE COOPERACIÓN',
    'Sustainable financing':'Financiamiento sostenible','Formal surge staffing':'Procedimiento formal de refuerzo de personal',
    'Updated surge roster':'Lista actualizada de personal de refuerzo',
    'Integrated information tools':'Herramientas de información integradas',
    'Structured information exchange':'Intercambio estructurado de información',
    'Reported countries':'Países con respuesta',
    # Capacity components
    'Core capacities reported as in place':'Capacidades esenciales reportadas como disponibles',
    'Country counts reflect only recognized answers to each survey item.':
      'Los conteos se basan en respuestas válidas a cada pregunta.',
    '01 / CAPACITY PROFILES':'01 / PERFILES DE CAPACIDADES',
    'Explore a component':'Explorar componente','Capacity availability':'Disponibilidad de capacidades',
    'Countries reporting each capacity':'Países que reportan cada capacidad',
    'Countries in this category':'Países en esta categoría',
    'Reported status by country':'Estado reportado por país',
    'Choose capacity':'Elegir capacidad','Country':'País','Reported capacity':'Capacidad reportada',
    'Colombia is counted once at regional level when at least one institution reports an in-place capacity.':
      'Colombia se cuenta una vez en el análisis regional cuando al menos una institución reporta la capacidad disponible.',
    'Information systems and surge workforce':'Sistemas de información y personal de refuerzo',
    'Key capacities for technical cooperation.':'Capacidades prioritarias para la cooperación técnica.',
    'Legal authority & governance':'Marco legal y gobernanza',
    'Policies, plans & procedures':'Políticas, planes y procedimientos',
    'Information systems & standards':'Sistemas y estándares de información',
    'Infrastructure & support':'Infraestructura y apoyo',
    'Human resources & surge':'Recursos humanos y refuerzo',
    'Infrastructure':'Infraestructura','Training (completed)':'Capacitación (realizada)',
    'Formal legal framework':'Marco legal formal', 'Decision-making enabled':'Capacidad formal de decisión',
    'Strategic committee established':'Comité estratégico establecido',
    'Formal intersectoral coordination':'Coordinación intersectorial formal',
    'High DRM integration':'Alta integración con gestión del riesgo',
    'Institutionally allocated finance':'Financiamiento institucional asignado',
    'National + subnational mandate':'Mandato nacional y subnacional',
    'In national response plan':'Incluido en el plan nacional de respuesta',
    'Manual or SOP available':'Manual o procedimiento operativo disponible',
    'Incident management system used':'Uso del sistema de manejo de incidentes',
    'Systematic risk assessment':'Evaluación sistemática del riesgo',
    'Incident action plan every activation':'Plan de acción para cada activación',
    'Documented roles':'Funciones documentadas',
    'Situation room integrated':'Sala situacional integrada',
    'Information management & monitoring':'Gestión de información y seguimiento',
    'Formal SITREP process':'Procedimiento formal para SITREP',
    'Structured exchange':'Intercambio estructurado de información',
    'Integrated/interoperable platform':'Plataforma integrada o interoperable',
    'Information gaps infrequent':'Brechas de información poco frecuentes',
    'Dedicated operations room':'Sala de operaciones exclusiva',
    'Virtual coordination space':'Espacio de coordinación virtual',
    'Backup power generator':'Planta eléctrica de respaldo',
    'Redundant internet connection':'Conexión redundante a internet',
    'Operational capacity to implement decisions':'Capacidad operativa para implementar decisiones',
    'Coordinator formally designated':'Coordinador designado formalmente',
    'Permanent staff on 24/7 duty':'Personal permanente de turno 24/7',
    'Formal surge procedure':'Procedimiento formal de refuerzo de personal',
    'Coordinates rapid response deployment':'Coordina el despliegue de respuesta rápida',
    'Formally participates in GHEC':'Participa formalmente en GHEC',
    'Updated deployable workforce mapping':'Mapeo actualizado de personal movilizable',
    # Operations
    'Hazards coordinated during the past two years':'Amenazas coordinadas durante los últimos dos años',
    'Categories reflect ordinal frequency bands, not exact event counts.':
        'Categorías de frecuencia ordinal, no números exactos de eventos.',
    '01 / TYPES OF EMERGENCIES':'01 / TIPOS DE EMERGENCIAS',
    'Physical infrastructure':'Infraestructura física',
    'Countries reporting these resources.':'Países que reportan estos recursos.',
    '02 / INFRASTRUCTURE':'02 / INFRAESTRUCTURA',
    'Training completed and prioritized':'Capacitación realizada y priorizada',
    'Each country counted once per course.':'Cada país se contabiliza una vez por tema.',
    '03 / WORKFORCE DEVELOPMENT':'03 / DESARROLLO DEL PERSONAL',
    'Training area':'Tema de capacitación','Last year':'Último año',
    'Next period':'Próximo período', 'Completed':'Realizada', 'Prioritized':'Prioritaria',
    'Completed last year':'Realizada el último año','Future priority':'Prioridad futura',
    # networks
    'Regional and global networks':'Redes regionales y mundiales',
    'Membership and interest among countries that answered these later survey questions.':
      'Participación e interés entre los países que respondieron las preguntas finales de la encuesta.',
    '01 / COOPERATION NETWORKS':'01 / REDES DE COOPERACIÓN',
    'countries answered':'países respondieron', 'participating':'participan',
    'interested':'interesados', 'not participating':'no participan',
    'Participating':'Participa','Interested':'Interesado','Not participating':'No participa',
    'See country-level network participation':'Ver participación en redes por país',
    'Expertise countries can share':'Capacidades que los países pueden compartir',
    'Technical expertise reported for cooperation.':'Capacidades técnicas reportadas para cooperación.',
    '02 / CAPACITIES OFFERED':'02 / CAPACIDADES OFRECIDAS',
    'How countries can cooperate':'Modalidades de cooperación entre países',
    'Reported modalities of technical collaboration.':'Modalidades reportadas de colaboración técnica.',
    '03 / MODALITIES':'03 / MODALIDADES',
    'The cooperation and network questions were completed by fewer countries. Each indicator uses the number of valid responses to that specific question.':
      'Las preguntas de cooperación y redes tienen menos respuestas. Cada indicador utiliza el número de respuestas válidas.',
    # country profile
    'Select a country':'Seleccionar país','Reporting institution':'Institución que responde',
    'Excel row':'Fila Excel','EOC status':'Estado del COE-S',
    'Activation time':'Tiempo de activación','24/7 duty staff':'Personal de turno 24/7',
    'Reported institutional capacities':'Capacidades institucionales reportadas',
    'Answers from this institution grouped by PHEOC core component.':
      'Respuestas institucionales agrupadas por componente esencial del COE-S.',
    '01 / REPORTED CAPACITIES':'01 / CAPACIDADES REPORTADAS',
    'Capacity':'Capacidad','Status':'Estado',
    'Only fully qualifying responses are classified as in place. Missing answers remain separate.':
      'Solo las respuestas plenamente afirmativas se clasifican como disponibles. Los datos faltantes se mantienen separados.',
    'Hazards coordinated':'Amenazas coordinadas','Frequency band for the selected institution.':
      'Intervalos de frecuencia de la institución seleccionada.',
    '02 / LAST TWO YEARS':'02 / ÚLTIMOS DOS AÑOS',
    'Hazard type':'Tipo de amenaza','Reported frequency':'Frecuencia reportada',
    'Resources the institution reports as available.':'Recursos que la institución reporta como disponibles.',
    '03 / INFRASTRUCTURE':'03 / INFRAESTRUCTURA',
    'Resource':'Recurso','Reported status':'Estado reportado',
    'Training and preparedness':'Capacitación y preparación',
    'Activities completed in the last year and priorities for the next period.':
      'Actividades realizadas el último año y prioridades del siguiente período.',
    '04 / PEOPLE AND TRAINING':'04 / PERSONAS Y CAPACITACIÓN',
    'Reported experience':'Experiencia reportada',
    'Original-language responses, without machine translation.':
      'Respuestas en su idioma original, sin traducción automática.',
    '05 / INSTITUTIONAL NOTES':'05 / NOTAS INSTITUCIONALES',
    'Reported strengths':'Fortalezas reportadas','Areas for improvement':'Áreas de mejora',
    'No narrative response provided.':'No se proporcionó respuesta narrativa.',
    'Recent events / activations · original response':'Eventos recientes / activaciones · respuesta original',
    'Technical capabilities and contributions this institution can offer':
      'Capacidades técnicas y contribuciones que puede ofrecer la institución',
    'Expertise:':'Capacidades técnicas:', 'Modalities:':'Modalidades:',
    'Each institution has its own response. Colombia’s two institutions remain separate.':
      'Cada institución conserva su respuesta. Las dos instituciones de Colombia permanecen separadas.',
    # common status / modes
    'In place':'Disponible','Partial / absent':'Parcial / ausente','Not reported':'Sin información',
    'Established':'Establecido','Not established':'No establecido',
    '24/7 continuous':'Continuo 24/7', 'Response + monitoring':'Respuesta y seguimiento',
    'Response only':'Solo respuesta','Not formally defined':'No definido formalmente',
    'Under 2 hours':'Menos de 2 horas','2–6 hours':'2–6 horas',
    'Over 6 hours':'Más de 6 horas','Not defined':'No definido',
    'No events':'Ningún evento','1–2 events':'1–2 eventos','3–5 events':'3–5 eventos',
    'More than 5 events':'Más de 5 eventos',
    'Initial':'Inicial', 'Developing':'En desarrollo',
    'Not reported / unknown':'Sin respuesta / desconocido',
    # Resource names
    'Dedicated room':'Sala exclusiva','Shared room':'Sala compartida',
    'Virtual coordination':'Coordinación virtual','Communications equipment':'Equipos de comunicaciones',
    'Display screens':'Pantallas','Backup generator':'Planta eléctrica de respaldo',
    'Redundant internet':'Internet redundante','Furniture':'Mobiliario',
    # Training areas
    'EOC activation':'Activación del COE-S','Incident management system':'Sistema de manejo de incidentes',
    'Information management':'Gestión de información',
    'Coordination & decisions':'Coordinación y toma de decisiones',
    'Damage & needs assessment':'Evaluación de daños y necesidades',
    'Rapid situation analysis':'Análisis rápido de situación',
    'Multidisciplinary response teams':'Equipos de respuesta multidisciplinarios',
    'After-action review':'Evaluación posterior a la acción',
    # Hazards
    'Geological / weather':'Geológicas / hidrometeorológicas',
    'Biological / epidemic':'Biológicas / epidemias',
    'Social / human-caused':'Sociales / origen humano',
    'Technological':'Tecnológicas',
    # Network names
    'EMT initiative':'Iniciativa EMT',
    # Expertise
    'Strategic leadership':'Liderazgo estratégico',
    'EOC strengthening':'Fortalecimiento de COE-S',
    'Incident management & coordination':'Gestión y coordinación de incidentes',
    'Surveillance & outbreak investigation':'Vigilancia e investigación de brotes',
    'Laboratory':'Laboratorio','Emergency Medical Teams':'Equipos Médicos de Emergencia',
    'Infection prevention & control':'Prevención y control de infecciones',
    'Risk communication':'Comunicación de riesgos',
    'Information & geospatial analysis':'Análisis de información y geoespacial',
    'Logistics & supplies':'Logística y suministros',
    'Water, sanitation & hygiene':'Agua, saneamiento e higiene',
    'Mental health & psychosocial support':'Salud mental y apoyo psicosocial',
    'Training & response evaluation':'Formación y evaluación de respuesta',
    'Exchange of experience':'Intercambio de experiencias',
    'Remote technical assistance':'Asistencia técnica remota',
    'Facilitators / instructors':'Facilitadores / instructores',
    'National expert mobilization':'Movilización de expertos nacionales',
    'Deployments to other countries':'Despliegue a otros países',
    'Mentoring':'Mentoría','Availability requires assessment':'Disponibilidad por evaluar',
    'The geographic layer could not be read. Check data/geografia/paises_americas.gpkg.':
      'No fue posible leer la capa geográfica. Revise data/geografia/paises_americas.gpkg.',
    'Map file not found. The Americas GeoPackage is expected in data/geografia/paises_americas.gpkg.':
      'No se encontró el mapa. Se espera el GeoPackage de las Américas en data/geografia/paises_americas.gpkg.',
    'PAHO / WHO · EOC-NET Americas · 2026  |  Self-reported information  |  Analytical dashboard for technical coordination':
      'OPS / OMS · EOC-NET Américas · 2026  |  Información autodeclarada  |  Tablero para la coordinación técnica',
    'Unable to read the survey data:':'No fue posible leer la encuesta:',
    # Misc
    'Brazil':'Brasil','Panama':'Panamá','Peru':'Perú','Saint Lucia':'Santa Lucía',
    'Belize':'Belice',
    'National Institute of Health (INS)':'Instituto Nacional de Salud (INS)',
    'National institute of health':'Instituto Nacional de Salud',
    'Ministry of Health and Social Protection':'Ministerio de Salud y Protección Social',
    'Ministry of Health':'Ministerio de Salud',
    'Secretariat of Health':'Secretaría de Salud',
    'Other reporting institution':'Otra institución que responde',
    'Reporting institution':'Institución que responde',
    'No survey response':'Sin respuesta a la encuesta',
    'Outside filter':'Fuera del filtro',
    'Survey respondents':'Países participantes',
    'Share of valid responses':'Porcentaje de respuestas válidas',
    'Countries with capacity':'Países con la capacidad',
    'Regional share':'Proporción regional',
    'Completed training':'Capacitación realizada',
    'Priority training':'Capacitación prioritaria',
    'No valid responses':'Sin respuestas válidas',
    'None':'Ninguno',
}


def tr(value, lang='en'):
    if value is None:
        return ''
    text=str(value)
    return ES.get(text,text) if lang=='es' else text


def chosen_language():
    """A stable, language-neutral state key prevents a language toggle from resetting views."""
    import streamlit as st
    return st.session_state.get('coe_language','en')


def T(value):
    return tr(value,chosen_language())