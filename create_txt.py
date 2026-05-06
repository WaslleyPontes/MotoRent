with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open('explicacao_app.txt', 'a', encoding='utf-8') as out:
    for i, line in enumerate(lines, 1):
        out.write(f"{i}: {line.rstrip()}\n")

print("Arquivo explicacao_app.txt criado com código numerado.")