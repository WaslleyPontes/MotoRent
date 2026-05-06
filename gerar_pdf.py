from fpdf import FPDF

def text_to_pdf(input_file, output_file):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip() == '':
                pdf.ln(5)  # Add some space for empty lines
            elif line.startswith('#'):
                pdf.set_font("Arial", 'B', 16)  # Bold for headers
                pdf.cell(200, 10, txt=line[1:].strip(), ln=True, align='L')
                pdf.set_font("Arial", size=12)  # Reset to normal
            elif line.startswith('##'):
                pdf.set_font("Arial", 'B', 14)  # Bold for subheaders
                pdf.cell(200, 10, txt=line[2:].strip(), ln=True, align='L')
                pdf.set_font("Arial", size=12)  # Reset to normal
            elif line.startswith('###'):
                pdf.set_font("Arial", 'B', 12)  # Bold for subsubheaders
                pdf.cell(200, 10, txt=line[3:].strip(), ln=True, align='L')
                pdf.set_font("Arial", size=12)  # Reset to normal
            else:
                pdf.multi_cell(0, 10, txt=line.strip())

    pdf.output(output_file)

if __name__ == "__main__":
    text_to_pdf("explicacao_completa.txt", "explicacao_completa.pdf")
    print("PDF gerado com sucesso!")</content>
<parameter name="filePath">c:\Users\wasll\Desktop\Nova pasta\gerar_pdf.py