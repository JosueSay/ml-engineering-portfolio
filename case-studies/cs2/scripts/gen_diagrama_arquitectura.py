# -*- coding: utf-8 -*-
"""Genera el .drawio de la arquitectura de datos de Puntos Bi.

Se ejecuta desde la raiz del caso: python3 scripts/gen_diagrama_arquitectura.py

Las coordenadas se calculan aqui para que el archivo sea regenerable y revisable
en un diff. Cada caja declara su nivel de confianza en el propio rotulo, con la
misma escala que gobierna el caso: publico, inferido o no publico.
"""
import html

CELDAS = []

# Paleta. El borde discontinuo marca lo inferido; el rojo, lo que no es publico
# o no se puede reconstruir.
ORIGEN     = "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;strokeWidth=2;fontSize=12;verticalAlign=top;spacingTop=4;"
ORIGEN_R   = "rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;strokeWidth=2;fontSize=12;verticalAlign=top;spacingTop=4;"
MOTOR      = "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;strokeWidth=2;fontSize=12;"
MOTOR_R    = "rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;strokeWidth=2;fontSize=12;"
MOTOR_INF  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;strokeWidth=2;dashed=1;fontSize=12;"
ELEG       = "rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;strokeWidth=2;dashed=1;fontSize=12;verticalAlign=top;spacingTop=4;"
LEDGER     = "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;fillColor=#d5e8d4;strokeColor=#82b366;strokeWidth=3;fontSize=13;verticalAlign=top;spacingTop=8;"
SALIDA     = "rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;strokeWidth=2;fontSize=12;verticalAlign=top;spacingTop=4;"
SALIDA_R   = "rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;strokeWidth=2;fontSize=12;verticalAlign=top;spacingTop=4;"
CANAL      = "rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;strokeWidth=1;fontSize=11;"
CAPA       = "rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;strokeWidth=2;fontSize=12;verticalAlign=top;spacingTop=4;"
GRUPO      = "rounded=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#9a9a9a;dashed=1;strokeWidth=1;fontSize=14;verticalAlign=top;spacingTop=6;fontStyle=1;align=center;"
DIAMANTE   = "rhombus;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;strokeWidth=2;fontSize=12;"
TITULO     = "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=26;fontStyle=1;"
SUBTITULO  = "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=top;fontSize=13;"
NOTA       = "rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#9a9a9a;strokeWidth=1;fontSize=12;align=left;verticalAlign=top;spacingLeft=10;spacingTop=8;"

ARISTA     = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#333333;strokeWidth=2;endArrow=block;endFill=1;fontSize=11;labelBackgroundColor=#ffffff;"
ARISTA_D   = ARISTA + "dashed=1;strokeColor=#b85450;"
ARISTA_G   = ARISTA + "strokeColor=#666666;strokeWidth=1;"


def rot(t):
    """Escapa y convierte los marcadores del rotulo a HTML de draw.io."""
    t = html.escape(t, quote=True)
    t = t.replace("**", "\x00")
    partes = t.split("\x00")
    salida = ""
    for i, p in enumerate(partes):
        salida += f"&lt;b&gt;{p}&lt;/b&gt;" if i % 2 else p
    return salida.replace("\n", "&lt;br&gt;")


def caja(ident, texto, x, y, w, h, estilo):
    CELDAS.append(
        f'        <mxCell id="{ident}" value="{rot(texto)}" style="{estilo}" vertex="1" parent="1">\n'
        f'          <mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" />\n'
        f'        </mxCell>'
    )


def flecha(ident, origen, destino, estilo=ARISTA, texto=""):
    CELDAS.append(
        f'        <mxCell id="{ident}" value="{rot(texto)}" style="{estilo}" edge="1" parent="1" source="{origen}" target="{destino}">\n'
        f'          <mxGeometry relative="1" as="geometry" />\n'
        f'        </mxCell>'
    )


# --------------------------------------------------------------------------
# Titulo
# --------------------------------------------------------------------------
caja("t1", "Arquitectura de datos del sistema de Puntos Bi", 40, 20, 1400, 40, TITULO)
caja("t2",
     "Reconstruida desde fuentes publicas de Corporacion BI. Cada elemento declara su nivel de confianza: "
     "**publico** si se cita de una fuente del emisor, **inferido** si se deduce de algo que si lo esta, "
     "**no publico** si el dato no existe en ninguna fuente.\n"
     "Ningun nombre de producto de infraestructura aparece en este diagrama: el banco no publica su stack, "
     "y suponerlo seria presentar una invencion como hallazgo.",
     40, 62, 1500, 48, SUBTITULO)

# --------------------------------------------------------------------------
# Columna A: sistemas de origen
# --------------------------------------------------------------------------
caja("gA", "Sistemas de origen", 40, 140, 320, 610, GRUPO)
caja("A1", "Autorizador de tarjetas\n**publico**\nUn evento por consumo. Por aqui entran seis de las ocho vias "
           "comerciales: Visa, debito Mastercard, credito Mastercard afiliada, Dividelo Todo, prepago Club Bi "
           "y comercios aliados.",
     60, 195, 280, 145, ORIGEN)
caja("A2", "Core de depositos\n**publico el umbral, no publica la tasa**\nNo reacciona a un evento sino al cierre "
           "de mes. Ahorro desde Q500, Monetaria desde Q1,000, 5 Estrellas desde Q1,000. Tres reglas distintas, "
           "ninguna publicada.",
     60, 355, 280, 145, ORIGEN_R)
caja("A3", "Motor de campanas\n**publico**\nMultiplicadores y bonificaciones con vigencia, padron de inscritos "
           "y topes propios.",
     60, 515, 280, 100, ORIGEN)
caja("A4", "Sorteos\n**publico**\nAcredita puntos que no derivan de ningun consumo. Disparo por SMS.",
     60, 630, 280, 100, ORIGEN_R)

# --------------------------------------------------------------------------
# Columna B: ingesta
# --------------------------------------------------------------------------
caja("B1", "Ingesta\n**publico**\nNinguna via es sincrona. La acreditacion tarda entre 48 y 72 horas habiles "
           "en todos los casos, lo que descarta un motor que reaccione a cada autorizacion.",
     400, 300, 250, 175, MOTOR_INF)

# --------------------------------------------------------------------------
# Columna C: elegibilidad y motor
# --------------------------------------------------------------------------
caja("C0", "Elegibilidad, se consulta al acreditar\n**publico**\nMembresia Club Bi vigente · servicio Bi Movil "
           "activo · la tarjeta acumula · afiliacion Mastercard solicitada.\nNo viaja en la transaccion: son "
           "estados que viven en otros sistemas.",
     700, 140, 560, 130, ELEG)

caja("gM", "Motor de acumulacion", 700, 300, 560, 450, GRUPO)
caja("M1", "Conversion de quetzales a dolares\n**no publico**: ni la tasa ni su fecha",
     725, 350, 510, 60, MOTOR_R)
caja("M2", "Rubro del comercio\n**inferido**: el mapa de codigos no es publico", 855, 430, 250, 80, DIAMANTE)
caja("M3", "Tasa base\n1 punto por US$1\n**publico**", 725, 535, 155, 65, MOTOR)
caja("M4", "Tasa reducida\n1 punto por US$10\n**publico**", 895, 535, 170, 65, MOTOR)
caja("M5", "Excluido\nretiros, extrafinanciamiento\n**inferido**", 1080, 535, 155, 65, MOTOR_INF)
caja("M6", "Acumuladores y topes\n**publico para cuatro categorias**\nTope anual: Gold y Premier 180,000 · "
           "Signature 360,000 · Infinite 420,000. Las demas categorias no publican tope. El grano del tope "
           "es pregunta abierta.",
     725, 625, 510, 105, MOTOR)

# --------------------------------------------------------------------------
# Columna D: ledger
# --------------------------------------------------------------------------
caja("D1", "Ledger de lotes\n**inferido**\nGrano: grupo familiar por periodo por origen.\nCada lote nace con "
           "su fecha de vencimiento y con la procedencia del punto, porque el valor de canje depende del "
           "producto que lo genero.",
     1310, 380, 280, 240, LEDGER)

# --------------------------------------------------------------------------
# Columna E: salidas
# --------------------------------------------------------------------------
caja("gE", "Salidas del punto", 1650, 140, 320, 610, GRUPO)
caja("E1", "Corte anual, 5 de febrero\n**publico**\nNo es vencimiento rodante: es fecha fija por anio de "
           "acumulacion. Vigencia efectiva de 13 a 25 meses.",
     1670, 195, 280, 130, SALIDA)
caja("E2", "Canje presencial\n**publico**\nTodo el catalogo. Exige tarjeta fisica y documento de identificacion.",
     1670, 345, 280, 110, SALIDA)
caja("E3", "Canje en linea\n**existe, alcance no publicado**\nEl portal tiene la funcionalidad; ninguna fuente "
           "dice que parte del catalogo admite.",
     1670, 475, 280, 115, SALIDA_R)
caja("E4", "Conversion a millas por telefono\n**la tasa no es publica**\nVaria segun el producto que genero el "
           "punto. Es lo que hace que el saldo no sea homogeneo.",
     1670, 610, 280, 120, SALIDA_R)

# --------------------------------------------------------------------------
# Columna F: canales de consulta
# --------------------------------------------------------------------------
caja("gF", "Consulta del saldo, seis canales", 2010, 140, 300, 610, GRUPO)
for i, (ident, texto) in enumerate([
    ("F1", "App Club Bi"),
    ("F2", "Bi en Linea, web"),
    ("F3", "Portal bipuntos, con identidad propia"),
    ("F4", "PBX 1717"),
    ("F5", "Estado de cuenta Bi Puntos"),
    ("F6", "Centros de canje"),
]):
    caja(ident, texto, 2030, 195 + i * 78, 260, 68, CANAL)
caja("F0", "Los seis muestran un numero unico sobre un saldo que no es homogeneo.",
     2030, 665, 260, 65, NOTA)

# --------------------------------------------------------------------------
# Aristas
# --------------------------------------------------------------------------
flecha("e1", "A1", "B1", ARISTA, "evento")
flecha("e2", "A2", "B1", ARISTA_D, "lote mensual")
flecha("e3", "B1", "M1")
flecha("e4", "M1", "M2")
flecha("e5", "M2", "M3", ARISTA, "resto de rubros")
flecha("e6", "M2", "M4", ARISTA, "cinco rubros")
flecha("e7", "M2", "M5", ARISTA, "excluido")
flecha("e8", "M3", "M6")
flecha("e9", "M4", "M6")
flecha("e10", "A3", "M6", ARISTA, "reglas con vigencia")
flecha("e11", "C0", "M6", ARISTA_D, "se consulta")
flecha("e12", "M6", "D1")
flecha("e13", "A4", "D1", ARISTA_D, "no derivable del consumo")
flecha("e14", "D1", "E1")
flecha("e15", "E1", "D1", ARISTA_D, "vencer es un asiento, no un borrado")
flecha("e16", "D1", "E2")
flecha("e17", "D1", "E3")
flecha("e18", "D1", "E4")
flecha("e19", "D1", "gF", ARISTA_G, "lectura")

# --------------------------------------------------------------------------
# Banda de correspondencia con la replica en miniatura
# --------------------------------------------------------------------------
caja("gG", "Correspondencia con la replica en miniatura del POC. Es lectura del equipo consultor, "
           "no una afirmacion sobre la implementacion del banco.",
     40, 800, 2270, 175, GRUPO)
caja("G1", "**Bronze**\nLo que entra tal como entra: reintentos del autorizador como filas repetidas, "
           "reversas como fila aparte, consumos sin codigo de rubro, montos en dos monedas y archivos "
           "fuera de orden.",
     70, 860, 580, 100, CAPA)
caja("G2", "**Silver**\nDeduplicado, reversas aplicadas, rubro resuelto y moneda convertida. Es la capa donde "
           "vive el riesgo: el mapa de rubros decide si un consumo acumula uno o un decimo.",
     680, 860, 580, 100, CAPA)
caja("G3", "**Gold**\nEl ledger de lotes y sus agregados. Cada lote conserva origen, fecha de vencimiento y "
           "los parametros con los que se acredito, que es lo que el sistema real no guarda y sin lo cual "
           "un saldo pasado no se puede reconstruir.",
     1290, 860, 1000, 100, CAPA)

# --------------------------------------------------------------------------
# Leyenda y notas
# --------------------------------------------------------------------------
caja("L1",
     "**Como leer este diagrama**\n\n"
     "Borde continuo azul, naranja o verde: **publico**, citable de una fuente de Corporacion BI.\n"
     "Borde discontinuo: **inferido**, se deduce de algo publicado pero no esta enunciado asi.\n"
     "Relleno rojo: el dato **no es publico** o el punto **no se puede reconstruir**.\n"
     "Flecha discontinua roja: camino que no se puede rederivar desde las transacciones.",
     40, 1005, 1100, 190, NOTA)
caja("L2",
     "**Las tres cosas que este diagrama dice y el folleto no**\n\n"
     "1. Ocho vias comerciales de acumulacion colapsan en cuatro origenes tecnicos, y cambiarle la tasa a "
     "uno no exige tocar los otros tres.\n"
     "2. Una acreditacion no es funcion del consumo: es funcion del consumo y de cuatro estados externos "
     "consultados en ese instante.\n"
     "3. Seis canales leen el saldo y tres lo ejecutan, pero toda la documentacion publica describe uno solo.",
     1200, 1005, 1110, 190, NOTA)

# --------------------------------------------------------------------------
# Archivo
# --------------------------------------------------------------------------
cuerpo = "\n".join(CELDAS)
xml = f'''<mxfile host="app.diagrams.net">
  <diagram name="Arquitectura de datos - Puntos Bi" id="puntos-bi-arquitectura">
    <mxGraphModel dx="2400" dy="1300" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="0" pageScale="1" pageWidth="2400" pageHeight="1250" math="0" shadow="1">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
{cuerpo}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
'''
import io
destino = "docs/architecture/diagrams/arquitectura-datos-puntos-bi.drawio"
io.open(destino, "w", encoding="utf-8").write(xml)
print("escrito:", destino)
print("celdas:", len(CELDAS))
