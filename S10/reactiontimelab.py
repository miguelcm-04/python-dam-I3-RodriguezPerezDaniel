import pygame
import time
import random
import json
import os
from enum import Enum

pygame.init()
ANCHO, ALTO = 1920, 1080
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("LaboratorioTiempoReaccion")
reloj = pygame.time.Clock()

# -------------------------------
# Rutas de imágenes
# -------------------------------
RUTA_S10 = "./S10"
fondo_menu = pygame.image.load(os.path.join(RUTA_S10,"Foto2.jpg")).convert()
fondo_menu = pygame.transform.scale(fondo_menu, (ANCHO, ALTO))
fondo_usuario = pygame.image.load(os.path.join(RUTA_S10,"Foto1.jpg")).convert()
fondo_usuario = pygame.transform.scale(fondo_usuario, (ANCHO, ALTO))
imagen_circulo = pygame.image.load(os.path.join(RUTA_S10,"foto3.jpg")).convert_alpha()
imagen_circulo = pygame.transform.scale(imagen_circulo, (140, 140))  # tamaño del círculo

# -------------------------------
# Cargar fuentes
# -------------------------------
RUTA_FUENTE = os.path.join(RUTA_S10,"ProFontIIxNerdFont-Regular.ttf")

def cargar_fuente(tamaño):
    """
    Carga una fuente desde archivo, o Arial como fallback.
    """
    try:
        return pygame.font.Font(RUTA_FUENTE, tamaño)
    except:
        return pygame.font.SysFont("Arial", tamaño)

FUENTES = {t: cargar_fuente(t) for t in [24,28,32,36,40,48,64,80,100]}

# -------------------------------
# Estados del juego
# -------------------------------
class EstadoJuego(Enum):
    USUARIO = 1
    MENU = 2
    ESPERANDO = 3
    CLIC = 4
    RESULTADO = 5
    PUNTUACIONES = 6
    SELECCION_DIFICULTAD = 7
    ENTRENAMIENTO_APUNTE = 8

# -------------------------------
# Dificultades
# -------------------------------
class Dificultad:
    """
    Representa una dificultad con nombre y rango de retraso para reacción.
    """
    def __init__(self,nombre,retraso_min,retraso_max):
        self.nombre = nombre
        self.retraso_min = retraso_min
        self.retraso_max = retraso_max

DIFICULTADES = {
    "Fácil": Dificultad("Fácil", 3.0, 6.0),
    "Normal": Dificultad("Normal", 2.0, 5.0),
    "Difícil": Dificultad("Difícil", 1.0, 4.0),
    "Extremo": Dificultad("Extremo", 0.5, 3.0)
}
dificultad_actual = DIFICULTADES["Normal"]

# -------------------------------
# Bases de datos
# -------------------------------
RUTA_DB_REACCION = os.path.join(RUTA_S10,"scores.json")
RUTA_DB_APUNTE = os.path.join(RUTA_S10,"aim_scores.json")

bd_reaccion = {"jugadores": {}}
bd_apunte = {"jugadores": {}}

def cargar_bd_reaccion():
    """
    Carga la base de datos de tiempos de reacción desde JSON.
    """
    global bd_reaccion
    if not os.path.exists(RUTA_DB_REACCION):
        guardar_bd_reaccion()
    try:
        with open(RUTA_DB_REACCION,"r") as f:
            bd_reaccion = json.load(f)
        if "jugadores" not in bd_reaccion:
            bd_reaccion = {"jugadores": {}}
    except:
        bd_reaccion = {"jugadores": {}}
        guardar_bd_reaccion()

def guardar_bd_reaccion():
    """Guarda la base de datos de tiempos de reacción en JSON."""
    with open(RUTA_DB_REACCION,"w") as f:
        json.dump(bd_reaccion,f,indent=4)

def cargar_bd_apunte():
    """
    Carga la base de datos de puntuaciones de Aim Training.
    """
    global bd_apunte
    if not os.path.exists(RUTA_DB_APUNTE):
        guardar_bd_apunte()
    try:
        with open(RUTA_DB_APUNTE,"r") as f:
            bd_apunte = json.load(f)
        if "jugadores" not in bd_apunte:
            bd_apunte = {"jugadores": {}}
    except:
        bd_apunte = {"jugadores": {}}
        guardar_bd_apunte()

def guardar_bd_apunte():
    """Guarda la base de datos de puntuaciones de Aim Training."""
    with open(RUTA_DB_APUNTE,"w") as f:
        json.dump(bd_apunte,f,indent=4)

def registrar_usuario(nombre):
    """
    Registra un usuario nuevo si no existe en ambas bases de datos.
    """
    if nombre not in bd_reaccion["jugadores"]:
        bd_reaccion["jugadores"][nombre] = float("inf")
    if nombre not in bd_apunte["jugadores"]:
        bd_apunte["jugadores"][nombre] = 0
    guardar_bd_reaccion()
    guardar_bd_apunte()

def actualizar_tiempo(nombre, tiempo):
    """
    Actualiza el mejor tiempo de reacción de un usuario.
    """
    if tiempo < bd_reaccion["jugadores"].get(nombre,float("inf")):
        bd_reaccion["jugadores"][nombre] = tiempo
        guardar_bd_reaccion()
        return True
    return False

def actualizar_puntuacion_apunte(nombre, puntos):
    """
    Actualiza la puntuación de Aim Training de un usuario si es mejor.
    """
    if puntos > bd_apunte["jugadores"].get(nombre, 0):
        bd_apunte["jugadores"][nombre] = puntos
        guardar_bd_apunte()

def obtener_todos_los_puntajes(modo="reaccion"):
    """
    Retorna todos los puntajes ordenados según modo.
    """
    if modo == "reaccion":
        jugadores = bd_reaccion["jugadores"]
        lista = [(jug, jugadores[jug] if jugadores[jug] != float("inf") else 9999) for jug in jugadores]
        lista.sort(key=lambda x: x[1])
    else:
        jugadores = bd_apunte["jugadores"]
        lista = [(jug, jugadores[jug]) for jug in jugadores]
        lista.sort(key=lambda x: x[1], reverse=True)
    return lista

cargar_bd_reaccion()
cargar_bd_apunte()

# -------------------------------
# Variables globales
# -------------------------------
estado = EstadoJuego.USUARIO
usuario = ""
texto_entrada = ""
mensaje = ""

tiempo_inicio = None
tiempo_fin = None
retraso_espera = None
inicio_retraso = None

btn_puntuaciones = pygame.Rect(ANCHO - 320, 50, 300, 70)
btn_usuario = pygame.Rect(50, 50, 300, 70)
btn_reaccion = pygame.Rect(ANCHO//2 - 150, ALTO//2 - 150, 300, 70)
btn_apunte = pygame.Rect(ANCHO//2 - 150, ALTO//2, 300, 70)
btn_dificultad = pygame.Rect(ANCHO//2 - 150, ALTO//2 + 150, 300, 70)

scroll_y = 0
VELOCIDAD_SCROLL = 40

# -------------------------------
# Funciones de interfaz
# -------------------------------
def dibujar_degradado(c1, c2):
    """Dibuja un fondo degradado vertical."""
    for y in range(ALTO):
        r = int(c1[0]*(1 - y / (ALTO-1)) + c2[0] * (y / (ALTO-1)))
        g = int(c1[1]*(1 - y / (ALTO-1)) + c2[1] * (y / (ALTO-1)))
        b = int(c1[2]*(1 - y / (ALTO-1)) + c2[2] * (y / (ALTO-1)))
        pygame.draw.line(pantalla, (r,g,b), (0,y), (ANCHO,y))

def texto_centrado(texto, y, tamaño=32, color=(255,255,255)):
    """Dibuja texto centrado horizontalmente en la pantalla."""
    fuente = FUENTES.get(tamaño, FUENTES[32])
    renderizado = fuente.render(texto, True, color)
    pantalla.blit(renderizado, renderizado.get_rect(center=(ANCHO//2, y)))

def dibujar_boton(rect, texto):
    """Dibuja un botón con texto, cambia de color al pasar el mouse."""
    hover = rect.collidepoint(pygame.mouse.get_pos())
    color_fondo = (255,255,255) if hover else (200,200,200)
    pygame.draw.rect(pantalla, color_fondo, rect, border_radius=15)
    pygame.draw.rect(pantalla, (0,0,0), rect, 3, border_radius=15)
    t = FUENTES[36].render(texto, True, (0,0,0))
    pantalla.blit(t, t.get_rect(center=rect.center))
    return hover

def dibujar_usuario():
    """Dibuja la pantalla de entrada de usuario."""
    pantalla.blit(fondo_usuario, (0, 0))
    texto_centrado("Introduce nombre de usuario:",300,48)
    pygame.draw.rect(pantalla,(255,255,255),(ANCHO//2 -200, ALTO//2 -25, 400,50), border_radius=15)
    txt = FUENTES[48].render(texto_entrada, True, (0,0,0))
    pantalla.blit(txt, (ANCHO//2 - 180, ALTO//2 - 20))

def dibujar_menu():
    """Dibuja el menú principal."""
    pantalla.blit(fondo_menu, (0, 0))
    texto_centrado("Demuestra tus reflejos",150,80)
    dibujar_boton(btn_reaccion,"Modo Reacción")
    dibujar_boton(btn_apunte,"Aim-Training")
    dibujar_boton(btn_dificultad,"Cambiar Dificultad")
    dibujar_boton(btn_puntuaciones,"Puntuaciones")
    txt = FUENTES[36].render(f"Usuario: {usuario}", True, (255,255,255))
    pantalla.blit(txt,(300,70))

def dibujar_espera(): # Miguel Ángel
    """Dibuja la pantalla de espera antes de reaccionar (simplificada)."""
    dibujar_degradado((20,20,20), (60,60,60))
    texto_centrado("¿PREPARADO?", 500, 64)
    # calcular puntos de animación (0..3). Si inicio_retraso es None -> 0
    puntos = int((time.time() - inicio_retraso) * 2) % 4 if inicio_retraso else 0
    texto_centrado("." * puntos, 600, 80)

def dibujar_click(): #Miguel Ángel 
    """Dibuja la pantalla donde se indica que hay que clicar (simplificada)."""
    dibujar_degradado((150,0,0), (80,0,0))
    texto_centrado("¡YA!", 500, 100)
    texto_centrado("Pulsa rápido", 650, 48)

def dibujar_resultado(): # Miguel Ángel
    """Dibuja la pantalla de resultado de reacción (simplificada)."""
    dibujar_degradado((0,160,100), (0,60,20))
    # calcular reacción con protección si faltan tiempos
    reaccion = round((tiempo_fin - tiempo_inicio), 3) if (tiempo_inicio and tiempo_fin) else 0.0
    texto_centrado("Tiempo de reacción:", 400, 64)
    texto_centrado(f"{reaccion} segundos", 550, 80)
    texto_centrado(mensaje, 650, 48)
    texto_centrado("Click o espacio para reiniciar", 750, 48)

def dibujar_puntajes(): # Miguel Ángel
    """Dibuja la pantalla de puntuaciones (simplificada)."""
    global scroll_y
    dibujar_degradado((10,10,40), (0,0,0))

    y = 100 + scroll_y
    texto_centrado("SCOREBOARD - REACCIÓN", y, 64)
    y += 80

    # obtener y dibujar puntajes de reacción (ordenados ascendente)
    for nombre, tiempo in obtener_todos_los_puntajes("reaccion"):
        texto_centrado(f"{nombre} - {round(tiempo,3)} s", y, 48)
        y += 60

    y += 80
    texto_centrado("SCOREBOARD - AIM TRAINING", y, 64)
    y += 80

    # obtener y dibujar puntajes de aim (ordenados descendente)
    for nombre, puntos in obtener_todos_los_puntajes("apunte"):
        texto_centrado(f"{nombre} - {round(puntos,2)} pts", y, 48)
        y += 60

    texto_centrado("Click o scroll para volver", ALTO - 60, 48)

# -------------------------------
# Manejo de eventos
# -------------------------------
def actualizar_usuario(evento):
    """Maneja la entrada de nombre de usuario."""
    global usuario, texto_entrada, estado
    if evento.type == pygame.KEYDOWN:
        if evento.key == pygame.K_RETURN:
            usuario = texto_entrada.strip().lower() or "guest"
            registrar_usuario(usuario)
            estado = EstadoJuego.MENU
        elif evento.key == pygame.K_BACKSPACE:
            texto_entrada = texto_entrada[:-1]
        elif evento.key == pygame.K_ESCAPE:
            pygame.quit()
            exit()
        else:
            if len(texto_entrada)<16:
                texto_entrada += evento.unicode

def iniciar_espera():
    """Inicia la espera aleatoria antes de reaccionar."""
    global retraso_espera, inicio_retraso, estado
    retraso_espera = random.uniform(dificultad_actual.retraso_min, dificultad_actual.retraso_max)
    inicio_retraso = time.time()
    estado = EstadoJuego.ESPERANDO

def actualizar_menu(evento):
    """Maneja eventos en el menú principal."""
    global estado, mensaje, texto_entrada
    if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
        x,y = evento.pos
        if btn_puntuaciones.collidepoint(x,y):
            estado = EstadoJuego.PUNTUACIONES
            return
        if btn_usuario.collidepoint(x,y):
            texto_entrada = ""
            estado = EstadoJuego.USUARIO
            return
        if btn_reaccion.collidepoint(x,y):
            iniciar_espera()
            return
        if btn_apunte.collidepoint(x,y):
            iniciar_entrenamiento_apunte()
            estado = EstadoJuego.ENTRENAMIENTO_APUNTE
            return
        if btn_dificultad.collidepoint(x,y):
            estado = EstadoJuego.SELECCION_DIFICULTAD
            return
    if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
        pygame.quit()
        exit()

def actualizar_esperando(evento):
    """Maneja eventos mientras se espera el inicio de la reacción."""
    global estado, mensaje
    if evento.type == pygame.MOUSEBUTTONDOWN:
        mensaje = "Muy pronto. Inténtalo de nuevo."
        estado = EstadoJuego.MENU
    if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
        pygame.quit()
        exit()

def actualizar_click(evento):
    """Maneja eventos cuando se espera el clic de reacción."""
    global tiempo_fin, estado, mensaje
    if evento.type == pygame.MOUSEBUTTONDOWN:
        tiempo_fin = time.time()
        reaccion = round(tiempo_fin - tiempo_inicio, 3)
        if actualizar_tiempo(usuario, reaccion):
            mensaje = f"Nueva marca: {reaccion}s"
        else:
            mensaje = f"Tiempo: {reaccion}s"
        estado = EstadoJuego.RESULTADO
    if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
        pygame.quit()
        exit()

def actualizar_resultado(evento):
    """Maneja eventos en la pantalla de resultados."""
    global estado
    if evento.type == pygame.MOUSEBUTTONDOWN or (evento.type == pygame.KEYDOWN and evento.key == pygame.K_SPACE):
        estado = EstadoJuego.MENU
    if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
        pygame.quit()
        exit()

def actualizar_puntajes(evento):
    """Maneja eventos en la pantalla de puntuaciones."""
    global estado, scroll_y
    if evento.type == pygame.MOUSEBUTTONDOWN:
        estado = EstadoJuego.MENU
    if evento.type == pygame.MOUSEWHEEL:
        scroll_y += -evento.y * VELOCIDAD_SCROLL
        scroll_y = max(min(scroll_y,0), -2000)
    if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
        pygame.quit()
        exit()

# -------------------------------
# Selector dificultad
# -------------------------------
botones_dificultad = []
etiquetas_dificultad = list(DIFICULTADES.keys())
def inicializar_ui_dificultad():
    """Inicializa botones para seleccionar dificultad."""
    global botones_dificultad
    botones_dificultad=[]
    y=300
    for etiqueta in etiquetas_dificultad:
        rect = pygame.Rect(ANCHO//2-150,y,300,70)
        botones_dificultad.append((etiqueta, rect))
        y+=120
inicializar_ui_dificultad()

def dibujar_dificultad():
    """Dibuja pantalla de selección de dificultad."""
    dibujar_degradado((30,30,30),(0,0,0))
    texto_centrado("Selecciona dificultad",200,80)
    for etiqueta, rect in botones_dificultad:
        dibujar_boton(rect,etiqueta)

def manejar_dificultad(evento):
    """Maneja eventos en pantalla de selección de dificultad."""
    global estado, dificultad_actual
    if evento.type == pygame.MOUSEBUTTONDOWN and evento.button==1:
        mx,my = evento.pos
        for etiqueta, rect in botones_dificultad:
            if rect.collidepoint(mx,my):
                dificultad_actual = DIFICULTADES[etiqueta]
                estado = EstadoJuego.MENU
    if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
        pygame.quit()
        exit()

# -------------------------------
# Entrenamiento de puntería
# -------------------------------
circulo_apunte = None
puntuacion_apunte = 0
inicio_circulo = None
activo_apunte = False
circulos_clicados = 0
TOTAL_CIRCULOS = 30

def iniciar_entrenamiento_apunte():
    """Inicia el entrenamiento de Aim Training."""
    global circulo_apunte, puntuacion_apunte, inicio_circulo, activo_apunte, circulos_clicados
    puntuacion_apunte = 0
    circulos_clicados = 0
    circulo_apunte = generar_circulo()
    inicio_circulo = time.time()
    activo_apunte = True

def generar_circulo():
    """Genera un círculo aleatorio dentro de la pantalla."""
    radio = 70
    x = random.randint(radio, ANCHO-radio)
    y = random.randint(200+radio, ALTO-100-radio)
    return pygame.Rect(x-radio, y-radio, radio*2, radio*2)

def actualizar_apunte(evento):
    """
    Maneja el entrenamiento de puntería:
    - Clic sobre círculo suma puntos
    - Clic fuera resta puntos
    """
    global circulo_apunte, puntuacion_apunte, inicio_circulo, activo_apunte, circulos_clicados, estado
    if not activo_apunte: return
    if evento.type == pygame.MOUSEBUTTONDOWN:
        mx,my = evento.pos
        if circulo_apunte.collidepoint(mx,my):
            tiempo_reaccion = time.time()-inicio_circulo
            puntos = max(0, round(10-tiempo_reaccion,2))
            puntuacion_apunte += puntos
            circulos_clicados += 1
            if circulos_clicados>=TOTAL_CIRCULOS:
                activo_apunte = False
                actualizar_puntuacion_apunte(usuario,int(puntuacion_apunte))
                estado = EstadoJuego.MENU
            else:
                circulo_apunte = generar_circulo()
                inicio_circulo = time.time()
        else:
            puntuacion_apunte -= 5
            if puntuacion_apunte<0:
                puntuacion_apunte = 0
    if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
        pygame.quit()
        exit()

def dibujar_apunte():
    """Dibuja pantalla de entrenamiento de puntería."""
    dibujar_degradado((0,0,0),(40,40,40))
    texto_centrado(f"Círculos restantes: {TOTAL_CIRCULOS-circulos_clicados}",100,64)
    texto_centrado(f"Puntuación: {round(puntuacion_apunte,2)}",200,48)
    if circulo_apunte:
        pantalla.blit(imagen_circulo, circulo_apunte.topleft)
    texto_centrado("Haz click en el círculo lo más rápido posible",300,48)

# -------------------------------
# Bucle principal
# -------------------------------
ejecutando = True
while ejecutando:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            ejecutando = False
            break
        if estado == EstadoJuego.USUARIO:
            actualizar_usuario(evento)
        elif estado == EstadoJuego.MENU:
            actualizar_menu(evento)
        elif estado == EstadoJuego.ESPERANDO:
            actualizar_esperando(evento)
        elif estado == EstadoJuego.CLIC:
            actualizar_click(evento)
        elif estado == EstadoJuego.RESULTADO:
            actualizar_resultado(evento)
        elif estado == EstadoJuego.PUNTUACIONES:
            actualizar_puntajes(evento)
        elif estado == EstadoJuego.SELECCION_DIFICULTAD:
            manejar_dificultad(evento)
        elif estado == EstadoJuego.ENTRENAMIENTO_APUNTE:
            actualizar_apunte(evento)

    # Verifica si terminó el tiempo de espera para iniciar clic
    if estado == EstadoJuego.ESPERANDO:
        if inicio_retraso and time.time()-inicio_retraso >= retraso_espera:
            tiempo_inicio = time.time()
            estado = EstadoJuego.CLIC

    # Dibujar según estado
    if estado == EstadoJuego.USUARIO:
        dibujar_usuario()
    elif estado == EstadoJuego.MENU:
        dibujar_menu()
    elif estado == EstadoJuego.ESPERANDO:
        dibujar_espera()
    elif estado == EstadoJuego.CLIC:
        dibujar_click()
    elif estado == EstadoJuego.RESULTADO:
        dibujar_resultado()
    elif estado == EstadoJuego.PUNTUACIONES:
        dibujar_puntajes()
    elif estado == EstadoJuego.SELECCION_DIFICULTAD:
        dibujar_dificultad()
    elif estado == EstadoJuego.ENTRENAMIENTO_APUNTE:
        dibujar_apunte()

    pygame.display.update()
    reloj.tick(60)
