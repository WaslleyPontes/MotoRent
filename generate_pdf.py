from fpdf import FPDF

# Lê o arquivo app.py
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Cria PDF
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=8)

line_num = 1
for line in lines:
    line = line.rstrip('\n')
    pdf.cell(0, 4, f"{line_num}: {line}", ln=True)
    line_num += 1

pdf.output("explicacao_app.pdf")
print("PDF gerado: explicacao_app.pdf")