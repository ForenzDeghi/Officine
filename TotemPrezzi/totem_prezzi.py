from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.core.image import Image as CoreImage
import io
import os
import pyodbc
import configparser
from PIL import Image as PilImage, ImageDraw, ImageFont
import ftplib

Window.size = (480, 640)

# Connessione a SQL Server
def connectToSql(cfg):
    config = configparser.ConfigParser()
    config.read('config.ini')
    params = config[cfg]
    try:
        conn = pyodbc.connect("DRIVER=ODBC Driver 17 for SQL Server;SERVER={0};DATABASE={1};UID={2};PWD={3};".format(
            params['host'], params['name'], params['user'], params['pass']
        ))
        return conn
    except Exception as e:
        print(e)
        exit(1)

class BarcodeApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=10)
        
        # Input per codice a barre
        self.barcode_input = TextInput(hint_text="Scansiona o inserisci il codice", multiline=False)
        self.barcode_input.bind(on_text_validate=self.fetch_data)  # Attiva scansione con "Invio"
        self.layout.add_widget(self.barcode_input)
        
        # Bottone di scansione
        self.scan_button = Button(text="Scansiona", on_press=self.fetch_data)
        self.layout.add_widget(self.scan_button)
        
        # Bottone di stampa etichette
        self.print_button = Button(text="Stampa Etichette", on_press=self.print_labels)
        self.layout.add_widget(self.print_button)
        
        # Etichetta di stato, posizionata molto in alto
        self.status_label = Label(text="", size_hint=(1, 0.1))
        self.layout.add_widget(self.status_label)
        
        # Widget di anteprima immagine molto più grande
        self.preview_image = Image(size_hint=(1, 1.5))
        self.layout.add_widget(self.preview_image)
        
        self.labels = []  # Lista per le etichette generate
        
        return self.layout

    def fetch_data(self, instance):
        barcode = self.barcode_input.text
        if not barcode:
            self.status_label.text = "Codice a barre vuoto."
            return
        
        # Connessione al database
        conn = connectToSql("RP")
        cursor = conn.cursor()
        query = '''SELECT TOP(1)
                    Articoli.[Codice Articolo] as Codice_Articolo,
                    Articoli.[Descrizione],
                    Articoli.[DescrizioneSuDocumenti],
                    [Prezzi di vendita].[Prezzo] * 1.22 * (1 - ISNULL(ListiniCondizioniSpeciali.ScontoExtra, 0) / 100.0) AS Prezzo_Aggiornato,
                    Barcodes.[Barcode],
                    Articoli.[CodProduttore],
                    Articoli.[ID articolo],
                    ListiniCondizioniSpeciali.ScontoExtra
                FROM
                    Articoli
                INNER JOIN
                    [Prezzi di vendita]
                    ON Articoli.[ID articolo] = [Prezzi di vendita].[ID articolo]
                INNER JOIN 
                    Barcodes
                    ON Barcodes.[ID articolo] = Articoli.[ID articolo]
                LEFT JOIN
                    ListiniCondizioniSpeciali
                    ON Articoli.[ID articolo] = ListiniCondizioniSpeciali.IdArticolo
                WHERE
                    [Prezzi di vendita].[ID listino] = 5
                    AND [Prezzi di vendita].[Prezzo] <> 0
                    AND Barcodes.[IdTipo] = 0
                    AND 
                    (
                        Articoli.[Codice Articolo] = ? 
                        OR Barcodes.[Barcode] = ?
                    )'''
        cursor.execute(query, barcode, barcode)
        result = cursor.fetchone()
        
        if result:
            self.create_label_image(result)
            self.status_label.text = "Etichetta creata per codice: {}".format(barcode)
        else:
            self.status_label.text = "Nessun dato trovato per il codice: {}".format(barcode)

    def create_label_image(self, data):
        base_image = PilImage.open("label_template.png")  # Immagine base
        draw = ImageDraw.Draw(base_image)

        # Crea una directory temporanea se non esiste
        temp_dir = "tmp_labels"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Caricamento font
        font_large = ImageFont.truetype("arial.ttf", 48)  # Font grande per il prezzo
        font_medium = ImageFont.truetype("arial.ttf", 18)  # Font medio per descrizione
        font_small = ImageFont.truetype("arial.ttf", 16)   # Font piccolo per codice articolo
        
        # Posizionamento della Descrizione in alto a sinistra (max 3 righe)
        descrizione = data.Descrizione
        max_width = 239  # Larghezza massima per riga
        lines = []
        words = descrizione.split()
        line = ""
        
        for word in words:
            test_line = f"{line} {word}".strip()
            if draw.textbbox((0, 0), test_line, font=font_medium)[2] <= max_width:
                line = test_line
            else:
                lines.append(line)
                line = word
            if len(lines) == 3:  # Limita a 3 righe
                break
        if line:
            lines.append(line)
        
        y_text = 10
        for line in lines:
            draw.text((10, y_text), line, font=font_medium, fill="white")
            y_text += draw.textbbox((0, 0), line, font=font_medium)[3] + 2  # Spaziatura tra le righe

        # Posizionamento del Codice Articolo più in basso senza "Codice:"
        codice_articolo = data.Codice_Articolo
        draw.text((10, base_image.height - 40), codice_articolo, font=font_small, fill="white")

        # Posizionamento del Prezzo Aggiornato più grande e centrato in basso
        prezzo_aggiornato = data.Prezzo_Aggiornato
        text_price = f"€ {prezzo_aggiornato:.2f}"
        bbox = draw.textbbox((0, 0), text_price, font=font_large)
        text_width = bbox[2]  # larghezza
        text_height = bbox[3]  # altezza
        draw.text((base_image.width - text_width - 10, base_image.height - text_height - 40), text_price, font=font_large, fill="white")

        # Salva l’immagine nel percorso temporaneo
        image_path = os.path.join(temp_dir, "label_{}.png".format(data.Barcode))
        base_image.save(image_path)
        self.labels.append(image_path)  # Aggiungi alla lista delle etichette

        # Mostra l'anteprima
        self.show_preview(base_image)

    def show_preview(self, image):
        # Converti l'immagine PIL in formato compatibile con Kivy
        data = io.BytesIO()
        image.save(data, format='png')
        data.seek(0)
        core_image = CoreImage(data, ext='png')
        
        # Aggiorna il widget dell'immagine di anteprima
        self.preview_image.texture = core_image.texture

    def print_labels(self, instance):
        if not self.labels:
            self.status_label.text = "Nessuna etichetta da stampare."
            return
        
        # Creazione di un file PDF con tutte le etichette
        from fpdf import FPDF
        pdf = FPDF()
        for label_path in self.labels:
            pdf.add_page()
            pdf.image(label_path, x=10, y=10, w=100, h=100)  # Regola le dimensioni dell'immagine come necessario

        pdf_output = "/tmp/labels_output.pdf"
        pdf.output(pdf_output)
        
        # Invio su FTP
        self.send_to_ftp(pdf_output)
        
        self.status_label.text = "Etichette salvate e inviate su FTP."
        self.labels = []  # Resetta la lista delle etichette

    def send_to_ftp(self, file_path):
        with ftplib.FTP("ftp.example.com") as ftp:
            ftp.login(user="username", passwd="password")
            with open(file_path, "rb") as file:
                ftp.storbinary(f"STOR /path/on/ftp/labels_output.pdf", file)

if __name__ == "__main__":
    BarcodeApp().run()
