"""Capas de datos: Bronze, Silver y Gold.

Bronze guarda la lectura tal como salió de la imagen, incluidas las
inválidas y su motivo de rechazo. Silver deja solo lo válido, ya fechado.
Gold añade las variables de modelado. La separación existe para poder
retroceder hasta el origen sin haberlo destruido.
"""
