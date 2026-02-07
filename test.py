import random

def generar_numeros_aleatorios():
    return [random.randint(0, 100) for _ in range(10)]

# Ejemplo de uso
numeros_aleatorios = generar_numeros_aleatorios()
print(numeros_aleatorios)
