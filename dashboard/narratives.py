"""Reviewed bilingual display text for public, nonpersonal survey narratives.

The Excel remains the source of truth. Entries are keyed by a stable record ID
and a short original-text prefix; an edited source answer falls back to its
original wording rather than displaying an outdated translation.
No personal names, email addresses or contact fields are used.
"""
from dashboard.i18n import tr

# For every edited response: expected beginning of the ORIGINAL source,
# followed by professionally edited Spanish and faithful English versions.
REVIEWED = {
    ('ARG-002', 'strengths'): (
        'esta en plena creación',
        'El COE se encuentra en proceso de conformación. Su principal fortaleza es el enfoque multidisciplinario, con participación de distintas áreas del Ministerio. Incorpora la central de monitoreo de la DINESA y nuevos dispositivos de despliegue territorial para apoyar la respuesta local de cada jurisdicción o provincia.',
        'The EOC is being established. Its main strength is a multidisciplinary approach involving different areas of the Ministry. It incorporates the DINESA monitoring center and newly established field deployment mechanisms that support local response in each jurisdiction or province.'
    ),
    ('ARG-002', 'improve'): (
        'Formalizar la creación del COE',
        'Formalizar la creación del COE mediante una resolución que le otorgue respaldo institucional; reglamentar su organización interna; y realizar capacitaciones periódicas sobre activación, elaboración de procedimientos y coordinación de despliegues.',
        'Formally establish the EOC through an institutional resolution; adopt internal organizational regulations; and provide periodic training on activation, procedure development, and deployment coordination.'
    ),
    ('BLZ-004', 'improve'): (
        '1. Simulations required',
        'Realizar simulacros de las emergencias más frecuentes en Belice; fortalecer la capacitación en gestión de incidentes (ICS), manejo de víctimas en masa (MCM) y diseño de ejercicios de simulación (SIMEX); y adquirir equipos de apoyo para el funcionamiento del COE.',
        'Conduct exercises for the emergencies most frequently experienced in Belize; strengthen training in the Incident Command System (ICS), mass casualty management (MCM), and the design of simulation exercises (SIMEX); and acquire equipment to support EOC operations.'
    ),
    ('BOL-005', 'strengths'): (
        '-Se encuentra establecida',
        'La estructura está establecida y tiene funciones definidas para las etapas anteriores, durante y posteriores a las emergencias. Cuenta con una entidad central que articula las áreas del Ministerio y otras instituciones. Realiza reuniones ordinarias y extraordinarias para evaluar riesgos y prepararse para la gestión interinstitucional.',
        'The structure is established, with defined responsibilities before, during, and after emergencies. A central entity coordinates the Ministry’s various units and other institutions. Regular and extraordinary meetings support risk assessment and interinstitutional preparedness.'
    ),
    ('BOL-005', 'improve'): (
        '-Mejorar la compatibilidad',
        'Mejorar la compatibilidad e interoperabilidad de los sistemas de información para apoyar la toma de decisiones; reducir la rotación del personal capacitado en los sistemas locales de salud; y perfeccionar los mecanismos de coordinación con las áreas de vigilancia epidemiológica, medicamentos y tecnologías sanitarias.',
        'Improve the compatibility and interoperability of information systems to support decision-making; reduce turnover of trained personnel in local health systems; and strengthen coordination mechanisms with epidemiological surveillance, medicines, and health technology units.'
    ),
    ('BRA-006', 'strengths'): (
        'Capacidade de articulação',
        'Capacidad de articulación intersectorial e interinstitucional entre los niveles federal, estatal y municipal del Sistema Único de Salud (SUS). Integración con los sistemas de vigilancia epidemiológica y monitoreo de eventos de importancia para la salud pública. Experiencia acumulada en la coordinación de respuestas ante emergencias, incluidas epidemias y desastres.',
        'Capacity for intersectoral and interinstitutional coordination across the federal, state, and municipal levels of Brazil’s Unified Health System (SUS). Integration with epidemiological surveillance and monitoring systems for public health events. Extensive experience coordinating emergency responses, including epidemics and disasters.'
    ),
    ('BRA-006', 'improve'): (
        'Formalização e institucionalização',
        'Formalizar e institucionalizar procedimientos operativos estandarizados para la activación y el funcionamiento del COE. Establecer un equipo permanente y mantener actualizado el registro de profesionales capacitados para la respuesta rápida. Fortalecer la infraestructura física y tecnológica destinada a la coordinación de emergencias.',
        'Formalize and institutionalize standard operating procedures for EOC activation and operation. Establish a permanent team and maintain an updated roster of professionals trained for rapid response. Strengthen the physical and technological infrastructure dedicated to emergency coordination.'
    ),
    ('COL-007', 'improve'): (
        '1. Capacitación en diferentes temas',
        'Capacitar a los posibles integrantes de los Equipos de Respuesta Inmediata (ERI) en distintas áreas. Asegurar la disponibilidad de insumos para despliegues simultáneos. Fortalecer la capacitación y la participación activa en GOARN. Incorporar herramientas de inteligencia artificial para apoyar la gestión del riesgo.',
        'Provide training across multiple topics for potential Immediate Response Team (ERI) members. Ensure sufficient supplies for simultaneous deployments. Strengthen training and active participation in GOARN. Incorporate artificial intelligence tools to support risk management.'
    ),
    ('COL-008', 'improve'): (
        'PROTOCOLOS Y PROCEDIMIENTOS',
        'Fortalecer los protocolos y procedimientos; mejorar el software y el hardware disponibles; y modernizar los sistemas de comunicaciones.',
        'Strengthen protocols and procedures; upgrade available software and hardware; and modernize communication systems.'
    ),
    ('DMA-009', 'improve'): (
        'Communication technology',
        'Mejorar la tecnología de comunicaciones, incluido el acceso a conectividad satelital (por ejemplo, Starlink), para mantener la capacidad de respuesta ante desastres naturales, como huracanes de categoría 5 o terremotos.',
        'Improve communication technology, including access to satellite connectivity (such as Starlink), to maintain response capabilities during natural disasters, including Category 5 hurricanes or earthquakes.'
    ),
    ('ECU-010', 'improve'): (
        '- Capacitación para toma',
        'Fortalecer la capacitación para la toma de decisiones estratégicas; desarrollar un Sistema de Comando de Incidentes para el sector salud; y mejorar la coordinación y la capacitación en los niveles territoriales.',
        'Strengthen training in strategic decision-making; develop an Incident Command System for the health sector; and improve coordination and training at subnational levels.'
    ),
    ('SLV-011', 'strengths'): (
        '1. Personal permanente',
        'Cuenta con personal permanente, un marco legal establecido e infraestructura y equipamiento.',
        'The institution has permanent staff, an established legal framework, and physical infrastructure and equipment.'
    ),
    ('SLV-011', 'improve'): (
        '1. Sistemas de gestión',
        'Fortalecer los sistemas de gestión de información, asegurar financiamiento para la sostenibilidad institucional y ampliar los recursos humanos disponibles.',
        'Strengthen information management systems, secure funding for institutional sustainability, and expand available human resources.'
    ),
    ('GTM-012', 'improve'): (
        "POE'S",
        'Desarrollar y fortalecer los procedimientos operativos estandarizados (POE), los sistemas de radiocomunicación y un sistema de información en tiempo real.',
        'Develop and strengthen standard operating procedures (SOPs), radio communication systems, and a real-time information system.'
    ),
    ('PAN-014', 'improve'): (
        'financiamiento directo',
        'Asegurar financiamiento directo para el CODES; adquirir equipamiento tecnológico y medios de transporte; fortalecer la comunicación satelital; y ampliar el espacio físico.',
        'Secure direct funding for CODES; acquire technological equipment and transportation resources; strengthen satellite communications; and expand physical space.'
    ),
    ('PRY-015', 'improve'): (
        '1. Fortalecimiento de la conectividad',
        '1. **Conectividad y telecomunicaciones críticas.** Durante emergencias climáticas intensas o en zonas rurales remotas, las redes comerciales de telefonía e internet pueden colapsar o no estar disponibles. Se requiere ampliar y consolidar una red de comunicaciones de emergencia robusta, con radios VHF/HF y enlaces satelitales autónomos, para mantener el flujo de información entre el COVE central o COE intersectorial, las regiones sanitarias y los equipos de respuesta rápida en terreno.\n\n2. **Sostenibilidad y descentralización del personal capacitado.** Los conocimientos especializados en el Sistema de Gestión de Incidentes (SGI) y la metodología EDAN Salud se concentran en el nivel central o en determinados equipos técnicos. Es prioritario establecer un programa continuo de capacitación y acreditación a nivel regional y local, de manera que los COE de Salud departamentales puedan activarse y operar autónomamente, de forma estandarizada y sin depender exclusivamente de equipos del nivel central.\n\n3. **Automatización e integración digital.** La recopilación, consolidación y validación manual de información de diversas instituciones puede retrasar los reportes de situación. Se necesita una plataforma interoperable para cargar datos desde dispositivos móviles en terreno y visualizarlos en tableros automatizados, facilitando la asignación de recursos e insumos médicos.',
        '1. **Critical connectivity and telecommunications.** During severe weather emergencies or in remote rural areas, commercial telephone and internet networks may collapse or be unavailable. A robust emergency communications network is needed, including VHF/HF radio systems and independent satellite links, to maintain uninterrupted information flow among the central COVE or intersectoral EOC, health regions, and rapid response teams in the field.\n\n2. **Sustainable and decentralized trained workforce.** Expertise in the Incident Management System (IMS) and the EDAN Salud health damage-and-needs assessment methodology is concentrated at the central level or within specific technical teams. An ongoing regional and local training and accreditation program is needed so departmental health EOCs can activate and operate independently and consistently, without relying solely on central-level deployments.\n\n3. **Digital automation and integration.** Manual collection, consolidation, and validation of information from multiple facilities can delay situation reports. An interoperable platform is needed to upload field data through mobile devices and display it on automated dashboards, enabling faster allocation of resources and medical supplies.'
    ),
    ('PER-016', 'improve'): (
        '1. Falta de innovación',
        'Modernizar la plataforma SIREED, que registra las emergencias y los desastres a nivel nacional. Reducir los efectos de la alta rotación de personal en los espacios nacionales de monitoreo. Ampliar la capacitación con cursos especializados para el personal.',
        'Modernize the SIREED platform, which records emergencies and disasters nationwide. Address high staff turnover in national monitoring units. Expand personnel training through specialized courses.'
    ),
    ('LCA-017', 'strengths'): (
        '- Established intra',
        'Coordinación establecida dentro de cada organismo y entre instituciones. Experiencia en preparación y respuesta ante emergencias. Integración con la estructura nacional de gestión de desastres y emergencias.',
        'Established intra-agency and interagency coordination. Experience in emergency preparedness and response. Integration with the national disaster and emergency management structure.'
    ),
    ('LCA-017', 'improve'): (
        '- need for dedicated staffing',
        'Contar con personal dedicado al COE de Salud Pública (PHEOC), ya que actualmente participan profesionales de distintos departamentos del Ministerio de Salud con múltiples funciones. Fortalecer la operación mediante protocolos documentados e incorporar herramientas tecnológicas que mejoren la recopilación, el intercambio y la actualización oportuna de la información situacional.',
        'Provide dedicated staffing for the Public Health Emergency Operations Center (PHEOC), whose current members are drawn from different Ministry of Health departments and have multiple responsibilities. Strengthen operations through documented protocols and introduce technological tools to improve data collection, sharing, and timely situational updates.'
    ),
}


def narrative_for_display(record_id, kind, original, language='en'):
    """Return reviewed prose only when it matches the corresponding source record."""
    value=str(original or '').strip()
    if not value:
        return tr('No narrative response provided.',language)
    match=REVIEWED.get((str(record_id),kind))
    if match is None:
        return value
    prefix,es,en=match
    # If the Excel changes, do not attach an old translation to a new answer.
    if not value.casefold().startswith(prefix.casefold()):
        return value
    return es if language=='es' else en
