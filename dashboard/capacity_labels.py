"""Validated short bilingual survey-choice labels for every capacity question.

Codes and wording verified against Encuesta_OPS_2026_COEs_con_Brasil.
Columns are ZERO-BASED Excel positions, as in dashboard.data.CAPACITIES.
Never guess from generic keywords: unknown responses remain identifiable.
"""
import re

# The key is the exact choice letter in each survey question.
OPTIONS = {
 -2: {'a':('Sí','Yes'),'b':('No','No'),'c':('Parcial / desarrollo','Partial / developing')},
 29: {'a':('Inexistente','Absent'),'b':('Inicial','Initial'),'c':('En desarrollo','Developing'),'d':('Funcional','Functional'),'e':('Consolidado','Consolidated')},
 32: {'a':('Inexistente','Absent'),'b':('Inicial','Initial'),'c':('En desarrollo','Developing'),'d':('Funcional','Functional'),'e':('Consolidado','Consolidated')},
 33: {'a':('Sí','Yes'),'b':('No','No')},
 36: {'a':('Inexistente','Absent'),'b':('Inicial','Initial'),'c':('En desarrollo','Developing'),'d':('Funcional','Functional'),'e':('Consolidado','Consolidated')},
 37: {'a':('Sí','Yes'),'b':('No','No'),'c':('Parcial / desarrollo','Partial / developing')},
 40: {'a':('Solo nacional','National only'),'b':('Nacional y subnacional','National & subnational'),'c':('No definido','Undefined')},
 41: {'a':('Sin coordinación','No coordination'),'b':('Ocasional','Occasional'),'c':('Formal y regular','Formal & regular'),'d':('No definido','Undefined')},
 42: {'a':('Sin integración','No integration'),'b':('Limitada','Limited'),'c':('Moderada','Moderate'),'d':('Alta','High')},
 43: {'a':('Sistemáticamente','Systematic'),'b':('Algunas veces','Sometimes'),'c':('No','No'),'d':('No sabe','Unknown')},
 46: {'a':('Formalizado','Formalized'),'b':('En formalización','Being formalized'),'c':('No','No'),'d':('No sabe','Unknown')},
 47: {'a':('Sí','Yes'),'b':('No','No')},
 49: {'a':('Sin evaluación','No assessment'),'b':('Limitada','Limited'),'c':('Parcial','Partial'),'d':('No sistemática','Not systematic'),'e':('Sistemática','Systematic')},
 50: {'a':('Inexistente','Absent'),'b':('Inicial','Initial'),'c':('En desarrollo','Developing'),'d':('Funcional','Functional'),'e':('Consolidado','Consolidated')},
 51: {'a':('Sí','Yes'),'b':('No','No')},
 66: {'a':('Designación formal','Formal appointment'),'b':('Designación informal','Informal appointment'),'c':('No','No')},
 68: {'a':('Formalizados','Formalized'),'b':('Sin formalizar','Not formalized'),'c':('No','No')},
 77: {'a':('Inexistente','Absent'),'b':('Inicial','Initial'),'c':('En desarrollo','Developing'),'d':('Funcional','Functional'),'e':('Consolidado','Consolidated')},
 78: {'a':('Actualizado','Updated'),'b':('Desactualizado','Outdated'),'c':('En implementación','Being implemented'),'d':('No','No'),'e':('No sabe','Unknown')},
 80: {'a':('Coordina formalmente','Formal coordination'),'b':('Participa / apoya','Supports coordination'),'c':('No coordina','No coordination'),'d':('No aplica / no sabe','N.A. / unknown')},
 81: {'a':('Coordina formalmente','Formal coordination'),'b':('Participa / apoya','Supports coordination'),'c':('No coordina','No coordination'),'d':('No se hace','Not implemented'),'e':('No aplica / no sabe','N.A. / unknown')},
 105: {'a':('Sin intercambio','No exchange'),'b':('Ocasional','Occasional'),'c':('Regular / parcial','Regular / partial'),'d':('Formal / estructurado','Formal / structured')},
 107: {'a':('Sin herramientas','No tools'),'b':('Herramientas básicas','Basic tools'),'c':('Sistemas institucionales','Institutional systems'),'d':('Plataformas integradas','Integrated platforms'),'e':('Interoperables','Interoperable')},
 108: {'a':('Crítico','Critical'),'b':('Alto','High'),'c':('Moderado','Moderate'),'d':('Bajo','Low')},
 109: {'a':('Sí','Yes'),'b':('No','No'),'c':('No sabe / no aplica','Unknown / N.A.')},
 110: {'a':('Sin SITREP','No SITREP'),'b':('Sin procedimiento','No procedure'),'c':('No sistemático','Not systematic'),'d':('Formal / regular','Formal / regular')},
}
RESOURCE_COLUMNS=frozenset(range(55,63))

def labels_for_question(column, responses, lang='en'):
    """Return faithful, unique category labels aligned to responses."""
    index=0 if lang=='es' else 1
    responses=list(responses)
    result=[]
    for response in responses:
        raw=str(response).strip()
        if raw=='__MIXED__':
            pair=('Respuestas diferentes','Different responses')
        elif column in RESOURCE_COLUMNS:
            pair=('Disponible','Available') if raw in ('1','1.0','True','true','Sí','Si') else ('No disponible','Not available')
        elif column==67:
            pair=(f'{raw} personas',f'{raw} staff')
        elif column==123:
            normalized=raw.casefold()
            if 'diseño' in normalized or 'desarrollo' in normalized:
                pair=('En desarrollo','Developing')
            elif 'actualiza periódicamente' in normalized:
                pair=('Actualizado','Updated')
            elif 'limitada' in normalized or 'no se actualiza' in normalized:
                pair=('Limitado / desactualizado','Limited / outdated')
            elif 'no existe' in normalized:
                pair=('No existe','Absent')
            else:
                raise ValueError(f'Unrecognized Q123 answer: {raw!r}')
        else:
            match=re.match(r'^([a-z])\s*[.)]\s*',raw,re.I)
            if not match:
                # Q15 stores text in the workbook but might lack a choice prefix.
                norm=raw.casefold()
                if column==-2 and norm in ('sí','si','yes','true'):
                    pair=('Sí','Yes')
                elif column==-2 and norm in ('no','false'):
                    pair=('No','No')
                else:
                    raise ValueError(f'Unrecognized answer for column {column}: {raw!r}')
            else:
                code=match.group(1).lower()
                try:
                    pair=OPTIONS[column][code]
                except KeyError as exc:
                    raise ValueError(f'Unmapped option {column}:{code}: {raw!r}') from exc
        result.append(pair[index])
    # Multiple institutions may report different categories for one country;
    # never hide distinct responses inside an arbitrary label.
    if len(set(result))<len(result):
        return [f'{label} ({i+1})' if result.count(label)>1 else label
                for i,label in enumerate(result)]
    return result
