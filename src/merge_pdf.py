from PyPDF2 import PdfReader, PdfWriter

def merge_pdfs(paths, output):
    pdf_writer = PdfWriter()

    for path in paths:
        pdf_reader = PdfReader(path)
        for page in range(len(pdf_reader.pages)):
            pdf_writer.add_page(pdf_reader.pages[page])

    with open(output, 'wb') as out:
        pdf_writer.write(out)

# Specify the paths to the PDFs you want to merge
paths = ['C:\\Users\\Omkar\\Downloads\\Rishi Minerals\\Offer letters\\Offer Letter Steelopedia_Boron.pdf','C:\\Users\\Omkar\\Downloads\\Rishi Minerals\\Specification sheet\\Furnace\\Rishi_Minerals_BoronOxidePremix_ProductSpec.pdf']
output_path = 'C:\\Users\\Omkar\\Downloads\\Rishi Minerals\\Specification sheet\\Furnace\\Steelopedia.pdf'
merge_pdfs(paths, output_path)
