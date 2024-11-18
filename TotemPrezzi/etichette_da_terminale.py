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
# import pyodbc  # Commentato perché non è più usato
import requests  # Per le chiamate HTTP all'API
import configparser
from PIL import Image as PilImage, ImageDraw, ImageFont
import ftplib
from fpdf import FPDF
from datetime import datetime
from configparser import ConfigParser

Window.size = (480, 640)

# # Connessione a SQL Server (Commentato)
# def connectToSql(cfg):
#     config = configparser.ConfigParser()
#     config.read('config.ini')
#     params = config[cfg]
#     try:
#         conn = pyodbc.connect("DRIVER=ODBC Driver 17 for SQL Server;SERVER={0};DATABASE={1};UID={2};PWD={3};".format(
#             params['host'], params['name'], params['user'], params['pass']
#         ))
#         return conn
#     except Exception as e:
#         print(e)
#         exit(1)

def filtra_descrizione(descrizione):
    termini_indesiderati = ["FP -", "*80*", "*ASSORTITO*", "*canvaspre*"]  # Sostituisci con i termini effettivi
    for termine in termini_indesiderati:
        descrizione = descrizione.replace(termine, "")
    return descrizione

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
        barcode = self.barcode_input.text.strip()
        if not barcode:
            self.status_label.text = "Codice a barre vuoto."
            return
        
        # # Connessione al database tramite pyodbc (Commentato)
        # conn = connectToSql("RP")
        # cursor = conn.cursor()
        # query = '''SELECT TOP(1)
        #             Articoli.[Codice Articolo] as Codice_Articolo,
        #             Articoli.[Descrizione],
        #             Articoli.[DescrizioneSuDocumenti],
        #             CAST(REPLACE([Prezzi di vendita].[Prezzo], ',', '.') AS FLOAT) * 1.22 * (1 - ISNULL(CAST(REPLACE(ListiniCondizioniSpeciali.ScontoExtra, ',', '.') AS FLOAT), 0) / 100.0) AS Prezzo_Aggiornato,
        #             Barcodes.[Barcode],
        #             Articoli.[CodProduttore],
        #             Articoli.[ID articolo],
        #             CAST(REPLACE(ListiniCondizioniSpeciali.ScontoExtra, ',', '.') AS FLOAT) AS ScontoExtra
        #         FROM
        #             Articoli
        #         INNER JOIN
        #             [Prezzi di vendita]
        #             ON Articoli.[ID articolo] = [Prezzi di vendita].[ID articolo]
        #         INNER JOIN 
        #             Barcodes
        #             ON Barcodes.[ID articolo] = Articoli.[ID articolo]
        #         LEFT JOIN
        #             ListiniCondizioniSpeciali
        #             ON Articoli.[ID articolo] = ListiniCondizioniSpeciali.IdArticolo
        #         WHERE
        #             [Prezzi di vendita].[ID listino] = 5
        #             AND [Prezzi di vendita].[Prezzo] <> 0
        #             AND Barcodes.[IdTipo] = 0
        #             AND 
        #             (
        #                 CAST(Articoli.[Codice Articolo] AS VARCHAR(50)) = ?
        #                 OR CAST(Barcodes.[Barcode] AS VARCHAR(50)) = ?
        #             )'''
        # cursor.execute(query, barcode, barcode)
        # result = cursor.fetchone()

        # Nuova logica per ottenere i dati tramite API
        #api_url = "http://integration.deghisupport.it:5000/api/officine/etichetta_prezzo"  # URL dell'API REST
        api_url = "http://192.168.1.241:5000/api/officine/etichetta_prezzo"  # URL dell'API REST
        params = {"barcode": barcode}  # Parametri per l'API
        try:
            response = requests.get(api_url, params=params)
            if response.status_code == 200:
                result_dict = response.json()
                result_dict["DescrizioneSuDocumenti"] = filtra_descrizione(result_dict["DescrizioneSuDocumenti"])
                self.create_label_image(result_dict)
                self.status_label.text = "Etichetta creata per codice: {}".format(barcode)
            else:
                self.status_label.text = "Errore API: codice {}".format(response.status_code)
        except Exception as e:
            self.status_label.text = f"Errore di connessione al server"
            print(f"Errore di connessione API: {e}")

    def create_label_image(self, data):
        base_image = PilImage.open("label_template.png")  # Immagine base
        draw = ImageDraw.Draw(base_image)

        # Crea una directory temporanea se non esiste
        temp_dir = "tmp_labels"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Caricamento font
        font_large = ImageFont.truetype("font\\Gilroy-Bold.ttf", 48)  # Font grande per il prezzo
        font_medium = ImageFont.truetype("font\\Gilroy-Medium.ttf", 18)  # Font medio per descrizione
        font_small = ImageFont.truetype("font\\Gilroy-Light.ttf", 12)   # Font piccolo per codice articolo
        font_strikethrough = ImageFont.truetype("font\\Gilroy-Medium.ttf", 18)  # Font medio barrato per il prezzo intero scontato
        font_discount = ImageFont.truetype("font\\Gilroy-Bold.ttf", 40)  # Font grande per il prezzo scontato
        
        # Posizionamento della Descrizione in alto a sinistra (max 2 righe)
        descrizione = data["DescrizioneSuDocumenti"]
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
            if len(lines) == 2:  # Limita a 2 righe
                break
        if line and len(lines) < 2:
            lines.append(line)
        
        y_text = 10
        for line in lines:
            draw.text((10, y_text), line, font=font_medium, fill="white")
            y_text += draw.textbbox((0, 0), line, font=font_medium)[3] + 2  # Spaziatura tra le righe

        # Posizionamento del Codice Articolo più in basso senza "Codice:"
        codice_articolo = data["Codice_Articolo"]
        draw.text((10, y_text), codice_articolo, font=font_small, fill="white")
        y_text += draw.textbbox((0, 0), codice_articolo, font=font_small)[3] + 10  # Aggiunge spazio per separare dal prezzo


        prezzo_aggiornato = data["Prezzo_Aggiornato"]
        sconto_extra = data["ScontoExtra"]
        prezzo_originale = prezzo_aggiornato / (1 - sconto_extra / 100) if sconto_extra else prezzo_aggiornato
        text_price = f"€ {prezzo_aggiornato:.2f}".replace('.', ',')

        if sconto_extra:  # Caso con sconto
            # Mostra il prezzo originale barrato sopra il prezzo scontato
            text_original_price = f"€ {prezzo_originale:.2f}".replace('.', ',')
            
            # Coordinate per il prezzo originale barrato allineato a destra
            bbox_original = draw.textbbox((0, 0), text_original_price, font=font_strikethrough)
            x_right = base_image.width - bbox_original[2] - 10  # Allineamento a destra
            y_price = base_image.height - y_text - bbox_original[3] - 30

            # Disegna il prezzo originale barrato
            draw.text((x_right, y_price), text_original_price, font=font_strikethrough, fill="white")
            
            # Linea barrata al centro del prezzo originale
            line_y = y_price + bbox_original[3] // 2
            draw.line((x_right, line_y, x_right + bbox_original[2], line_y), fill="white", width=2)

            # Posiziona il prezzo scontato in grande sotto il prezzo barrato
            bbox_discount = draw.textbbox((0, 0), text_price, font=font_discount)
            draw.text((base_image.width - bbox_discount[2] - 10, y_price + bbox_original[3] + 5), text_price, font=font_discount, fill="white")
        else:  # Caso senza sconto
            # Mostra solo il prezzo intero
            bbox = draw.textbbox((0, 0), text_price, font=font_large)
            draw.text((base_image.width - bbox[2] - 10, base_image.height - bbox[3] - y_text), text_price, font=font_large, fill="white")

        # Salva l’immagine nel percorso temporaneo
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        image_path = os.path.join(temp_dir, "label_{}_{}.png".format(data["Barcode"], timestamp))
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
        
        # Percorso di salvataggio del PDF
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_dir = "tmp"
        pdf_output = os.path.join(output_dir, "labels_output_{}.pdf".format(timestamp))
        
        # Crea la cartella se non esiste
        os.makedirs(output_dir, exist_ok=True)
        
        # Configurazione della pagina e delle etichette
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        label_width = 60  # Larghezza dell'etichetta in mm
        label_height = 40  # Altezza dell'etichetta in mm
        margin_x = 10  # Margine sinistro e destro in mm
        margin_y = 10  # Margine superiore e inferiore in mm
        labels_per_row = 3  # Numero di etichette per riga
        page_width = 210  # Larghezza della pagina A4 in mm
        page_height = 297  # Altezza della pagina A4 in mm

        # Coordinate iniziali per la prima etichetta
        x = margin_x
        y = margin_y

        # Aggiungi la prima pagina
        pdf.add_page()

        for label_path in self.labels:
            # Aggiungi l'etichetta alla posizione corrente
            pdf.image(label_path, x=x, y=y, w=label_width, h=label_height)

            # Aggiorna la posizione x per la prossima etichetta
            x += label_width

            # Se abbiamo raggiunto il limite di etichette per riga, resettiamo x e incrementiamo y
            if x + label_width > page_width - margin_x:
                x = margin_x  # Torna all'inizio della riga
                y += label_height  # Passa alla riga successiva

            # Se lo spazio verticale si esaurisce, aggiungi una nuova pagina e resetta le coordinate
            if y + label_height > page_height - margin_y:
                pdf.add_page()
                x = margin_x
                y = margin_y

        # Salva il PDF
        pdf.output(pdf_output)
        
        # Invio su FTP
        self.send_to_ftp(pdf_output)
        
        self.status_label.text = "Etichette salvate e inviate su FTP."
        self.labels = []  # Resetta la lista delle etichette
        
    def send_to_ftp(self, file_path):

        config = ConfigParser()
        config_file = 'config.ini'
        config.read(config_file)

        ftp_config = {
        'host': config['ftp_off']['host'],
        'user': config['ftp_off']['user'],
        'pass': config['ftp_off']['pass'],
        'directory': config['ftp_off']['directory']
    }

        ftp_dir = ftp_config["directory"]  # Directory di destinazione sul server FTP

        with ftplib.FTP(ftp_config["host"]) as ftp:
            ftp.login(user=ftp_config["user"], passwd=ftp_config["pass"])

            # Naviga attraverso ogni sottocartella in ftp_dir e crea se necessario
            for folder in ftp_dir.strip("/").split("/"):
                try:
                    ftp.cwd(folder)  # Prova a entrare nella cartella
                except ftplib.error_perm:
                    ftp.mkd(folder)  # Crea la cartella se non esiste
                    ftp.cwd(folder)  # Entra nella cartella appena creata

            # Caricamento del file nella directory FTP finale
            with open(file_path, "rb") as file:
                ftp.storbinary(f"STOR {os.path.basename(file_path)}", file)


if __name__ == "__main__":
    BarcodeApp().run()
