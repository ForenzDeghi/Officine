from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.core.image import Image as CoreImage
from kivy.uix.popup import Popup
import io
import os
import requests  # Per le chiamate HTTP all'API
from PIL import Image as PilImage, ImageDraw, ImageFont
import ftplib
from fpdf import FPDF
from datetime import datetime
from configparser import ConfigParser
import sys
from io import BytesIO
#
#
# Commentati perchè spaccano apk su mobile
#
#
#
# from reportlab.graphics.barcode import code128
# from reportlab.pdfgen import canvas
# from reportlab.graphics import renderPM
# from kivy.uix.widget import Widget
# from barcode import Code128
# from barcode.writer import ImageWriter

#Window.size = (480, 640)

def get_asset_path(filename):
    # Ritorna il path corretto di un file asset.
    if hasattr(sys, "_MEIPASS"):
        # Path degli asset quando è in esecuzione l'eseguibile PyInstaller
        return os.path.join(sys._MEIPASS, "assets", filename)
    else:
        # Path degli asset durante lo sviluppo
        return os.path.join("assets", filename)

def filtra_descrizione(descrizione):
    termini_indesiderati = ["FP -", "*80*", "*ASSORTITO*", "*canvaspre*"]  # Sostituisci con i termini effettivi
    for termine in termini_indesiderati:
        descrizione = descrizione.replace(termine, "")
    return descrizione







class BarcodeApp(App):

    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=5)
        
        # Input per codice a barre
        self.barcode_input = TextInput(hint_text="Scansiona o inserisci il codice", multiline=False)
        self.barcode_input.bind(on_text_validate=self.fetch_data)  # Attiva scansione con "Invio"
        self.layout.add_widget(self.barcode_input)
        
        # Bottone di scansione
        #self.scan_button = Button(text="Scansiona", size_hint=(1, None), font_size=18, height=60)
        #self.scan_button = Button(text="Scansiona", size_hint=(1, 0.15))
        self.scan_button = Button(text="Scansiona", on_press=self.fetch_data)
        self.layout.add_widget(self.scan_button)
        
        # Bottone di stampa etichette
        #self.print_button = Button(text="Stampa Etichette", size_hint=(1, None), font_size=18, height=60)
        #self.print_button = Button(text="Stampa Etichette", size_hint=(1, 0.15))
        self.print_button = Button(text="Stampa Etichette", on_press=self.print_labels)
        self.layout.add_widget(self.print_button)

        # Bottone per annullare le etichette
        #self.cancel_button = Button(text="Annulla etichette", size_hint=(1, None), font_size=14, height=40)
        #self.cancel_button = Button(text="Annulla etichette", size_hint=(1, 0.08))
        self.cancel_button = Button(text="Annulla Lista", on_press=self.cancel_labels)
        self.layout.add_widget(self.cancel_button)
        
        # Etichetta di stato, posizionata molto in alto
        self.status_label = Label(text="", size_hint=(1, 0.1))
        self.layout.add_widget(self.status_label)
        
        # Widget di anteprima immagine molto più grande
        self.preview_image = Image(size_hint=(1, 1.5))
        self.layout.add_widget(self.preview_image)

        # Contatore delle etichette
        self.label_counter = 0
        self.counter_label = Label(text=f"Etichette: {self.label_counter}", size_hint=(1, 0.1), halign="right")
        self.layout.add_widget(self.counter_label)
        
        self.labels = []  # Lista per le etichette generate
        
        return self.layout

    def cancel_labels(self, instance):
        #Resetta tutte le etichette non ancora inviate e aggiorna lo stato.
        self.labels = []  # Resetta la lista delle etichette
        self.reset_counter()  # Resetta il contatore delle etichette
        self.status_label.text = "Tutte le etichette annullate."

    def update_counter(self):
        #Aggiorna il contatore delle etichette.
        self.label_counter += 1
        self.counter_label.text = f"Etichette: {self.label_counter}"
    
    def reset_counter(self):
        #Reimposta il contatore delle etichette.
        self.label_counter = 0
        self.counter_label.text = f"Etichette: {self.label_counter}"

    def fetch_data(self, instance):
        barcode = self.barcode_input.text.strip()
        self.barcode_input.text = "" # Ripulisce il campo di testo alla pressione del tasto
        if not barcode:
            self.status_label.text = "Codice a barre vuoto."
            return
        
        # Nuova logica per ottenere i dati tramite API
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
            self.status_label.text = f"Errore: {e.args[0]}" if e.args else "Errore sconosciuto"
            print(f"Errore di connessione API: {e}")


    



    def create_label_image(self, data):
        base_image_path = get_asset_path("label_template.png")
        base_image = PilImage.open(base_image_path) # Immagine base
        draw = ImageDraw.Draw(base_image)

        # Crea una directory temporanea se non esiste --------> Originale
        # temp_dir = os.path.join(os.getcwd(), "tmp_labels")
        # os.makedirs(temp_dir, exist_ok=True)

        # **MODIFICA**: Usa un percorso compatibile con Android, altrimenti rispetta quello di sistema
        temp_dir = os.path.join(os.environ.get('ANDROID_PRIVATE', os.getcwd()), "tmp_labels")
        os.makedirs(temp_dir, exist_ok=True)  # Crea la directory temporanea se non esiste
        print(f"Percorso temporaneo: {temp_dir}")  # Log per debug
            
        # Caricamento font
        font_large = ImageFont.truetype(get_asset_path("font/Gilroy-Bold.ttf"), 48)  # Font grande per il prezzo
        font_medium = ImageFont.truetype(get_asset_path("font/Gilroy-Medium.ttf"), 18)  # Font medio per descrizione
        font_small = ImageFont.truetype(get_asset_path("font/Gilroy-Light.ttf"), 15)   # Font piccolo per codice articolo
        font_strikethrough = ImageFont.truetype(get_asset_path("font/Gilroy-Medium.ttf"), 24)  # Font medio barrato per il prezzo intero scontato
        font_discount = ImageFont.truetype(get_asset_path("font/Gilroy-Bold.ttf"), 36)  # Font grande per il prezzo scontato
        
       
        # Inizio blocco per generazione barcode
        codice_articolo = data["Codice_Articolo"]

        # Chiamata API per generare barcode Code-128
        api_url = f"http://192.168.1.182:5000/generate_barcode?barcode={codice_articolo}"



        try:
            # Richiesta all'API per ottenere l'immagine del barcode
            response = requests.get(api_url)
            if response.status_code == 200:
                # Carica l'immagine del barcode direttamente dal contenuto della risposta
                barcode_image = PilImage.open(BytesIO(response.content))
                print(f"Barcode dimensioni originali: {barcode_image.size}")  # **Log per debug**

                # Calcola l'area da ritagliare (eliminando il testo nella parte inferiore)
                original_width, original_height = barcode_image.size
                crop_height = int(original_height * 0.74)  # Mantieni solo il 75% superiore dell'immagine
                barcode_image = barcode_image.crop((0, 0, original_width, crop_height))

                # Dimensioni personalizzate per il barcode
                custom_barcode_width = 239  # Larghezza del barcode
                custom_barcode_height = 38  # Altezza del barcode
                barcode_image = barcode_image.resize((custom_barcode_width, custom_barcode_height), PilImage.LANCZOS)
                print(f"Dimensioni barcode ritagliato: {barcode_image.size}")  # **Log per debug**

                # **MODIFICA**: Salva temporaneamente il barcode
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                barcode_path = os.path.join(temp_dir, f"barcode_{timestamp}.png")
                barcode_image.save(barcode_path)
                print(f"Barcode salvato temporaneamente in: {barcode_path}")  # **Log per debug**

                # Padding personalizzato per ogni lato
                padding_top = 2       # Margine superiore
                padding_right = 2    # Margine destro
                padding_bottom = 2  # Margine inferiore (maggiore)
                padding_left = 2      # Margine sinistro

                white_bg_width = custom_barcode_width + padding_left + padding_right
                white_bg_height = custom_barcode_height + padding_top + padding_bottom

                # Calcola la posizione per centrare il rettangolo bianco in basso
                barcode_x = (base_image.width - white_bg_width) // 2
                barcode_y = base_image.height - white_bg_height - 8

                # Disegna il rettangolo bianco come sfondo
                draw = ImageDraw.Draw(base_image)
                draw.rectangle(
                    [barcode_x, barcode_y, barcode_x + white_bg_width, barcode_y + white_bg_height],
                    fill="white"  # Colore dello sfondo bianco
                )

                # Posiziona il barcode all'interno del rettangolo bianco con padding personalizzato
                barcode_x_inner = barcode_x + padding_left
                barcode_y_inner = barcode_y + padding_top
                base_image.paste(barcode_image, (barcode_x_inner, barcode_y_inner))

            else:
                print(f"Errore API: {response.status_code}, {response.text}")  # **Log per debug**
        except Exception as e:
            print(f"Errore durante la generazione del barcode: {e}")  # **Log per debug**
        # Fine blocco per generazione barcode




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

        # Aggiungi una riga vuota se la descrizione è composta da una sola riga
        if len(lines) == 1:
            lines.append(" ")
        
        y_text = 10
        for line in lines:
            draw.text((10, y_text), line, font=font_medium, fill="white")
            y_text += draw.textbbox((0, 0), line, font=font_medium)[3] + 2  # Spaziatura tra le righe

        # Incrementa la distanza tra la descrizione e il codice articolo
        extra_spacing = 10  # Spazio extra tra descrizione e codice articolo
        y_text += extra_spacing

        # Posizionamento del Codice Articolo più in basso senza "Codice:"
        codice_articolo = data["Codice_Articolo"]
        draw.text((10, y_text), codice_articolo, font=font_small, fill="white")
        y_text += draw.textbbox((0, 0), codice_articolo, font=font_small)[3]  # Aggiunge spazio per separare dal prezzo


        prezzo_aggiornato = data["Prezzo_Aggiornato"]
        sconto_extra = data["ScontoExtra"]
        sconto_percentuale = f"-{int(sconto_extra)}%" if sconto_extra else ""  # Sconto percentuale se presente
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
            draw.text((x_right, y_price), text_original_price, font=font_strikethrough, fill="red")
            
            # Linea barrata al centro del prezzo originale
            line_y = y_price + bbox_original[3] // 2
            draw.line((x_right, line_y, x_right + bbox_original[2], line_y), fill="white", width=1)

            # Posiziona il prezzo scontato in grande sotto il prezzo barrato
            # bbox_discount = draw.textbbox((0, 0), text_price, font=font_discount)
            # draw.text((base_image.width - bbox_discount[2] - 10, y_price + bbox_original[3] + 5), text_price, font=font_discount, fill="white")

            # bbox_discount = draw.textbbox((0, 0), sconto_percentuale, font=font_discount)
            # draw.text((base_image.width - bbox_discount[2] - 10, y_price + bbox_original[3] + 5), sconto_percentuale, font=font_discount, fill="red")

            # Posiziona il prezzo scontato in grande sotto il prezzo barrato
            bbox_discount = draw.textbbox((0, 0), text_price, font=font_discount)
            draw.text((base_image.width - bbox_discount[2] - 10, y_price + bbox_original[3] + 5), text_price, font=font_discount, fill="white")

            bbox_discount = draw.textbbox((0, 0), sconto_percentuale, font=font_discount)
            #draw.text((base_image.width - bbox_discount[2] - 50 - bbox_discount[2], y_price + bbox_original[3] + 5), sconto_percentuale, font=font_discount, fill="red")
            draw.text((10, y_price + bbox_original[3] + 5), sconto_percentuale, font=font_discount, fill="red")

        else:  # Caso senza sconto
            # Mostra solo il prezzo intero
            bbox = draw.textbbox((0, 0), text_price, font=font_large)
            draw.text((base_image.width - bbox[2] - 10, base_image.height - bbox[3] - y_text), text_price, font=font_large, fill="white")

        # Salva l’immagine nel percorso temporaneo -------> Originale
        # timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        # image_path = os.path.join(temp_dir, "label_{}_{}.png".format(data["Barcode"], timestamp))
        # base_image.save(image_path)
        # self.labels.append(image_path)  # Aggiungi alla lista delle etichette

        # **MODIFICA**: Salva il template aggiornato nel percorso temporaneo
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        image_path = os.path.join(temp_dir, f"label_{data['Barcode']}_{timestamp}.png")
        base_image.save(image_path)
        print(f"Etichetta salvata in: {image_path}")  # **Log per debug**
        self.labels.append(image_path)

        # Aggiorna il contatore delle etichette
        self.update_counter()

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

    def show_filename_popup(self):
        # Layout del popup
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Campo di testo per il nome del file
        filename_input = TextInput(hint_text="Inserisci il nome del file", multiline=False)
        layout.add_widget(filename_input)
        
        # Bottone per confermare
        confirm_button = Button(text="Conferma", size_hint=(1, 0.2))
        layout.add_widget(confirm_button)
        
        # Popup
        popup = Popup(title="Nome del file PDF", content=layout, size_hint=(0.8, 0.4))
        
        # Evento per il bottone
        confirm_button.bind(on_press=lambda x: self.on_filename_confirm(popup, filename_input.text))
        
        # Mostra il popup
        popup.open()

    def on_filename_confirm(self, popup, filename):
        if not filename.strip():
            self.status_label.text = "Nome del file non può essere vuoto."
            return
        
        # Chiude il popup
        popup.dismiss()
        
        # Imposta il nome del file
        self.generate_and_upload_pdf(filename.strip())

    def generate_and_upload_pdf(self, filename):
        # Percorso di salvataggio del PDF
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_dir = os.path.join(os.getcwd(), "tmp")
        pdf_output = os.path.join(output_dir, f"{filename}_{timestamp}.pdf")
        
        # Crea la cartella se non esiste
        os.makedirs(output_dir, exist_ok=True)
        
        # Configurazione della pagina e delle etichette
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        label_width = 60  # Larghezza dell'etichetta in mm
        label_height = 40  # Altezza dell'etichetta in mm
        margin_x = 15  # Margine sinistro e destro in mm
        margin_y = 8  # Margine superiore e inferiore in mm
        labels_per_row = 3  # Numero di etichette per riga
        page_width = 210  # Larghezza della pagina A4 in mm
        page_height = 297  # Altezza della pagina A4 in mm

        # Coordinate iniziali per la prima etichetta
        x = margin_x
        y = margin_y

        # Aggiungi la prima pagina
        pdf.add_page()

        indice_ciclo_etichette = 1

        for label_path in self.labels:
            # Aggiungi l'etichetta alla posizione corrente
            pdf.image(label_path, x=x, y=y, w=label_width, h=label_height)

            # Aggiorna la posizione x per la prossima etichetta
            x += label_width

            # Se abbiamo raggiunto il limite di etichette per riga, resettiamo x e incrementiamo y
            if x + label_width > page_width - margin_x:
                x = margin_x  # Torna all'inizio della riga
                y += label_height  # Passa alla riga successiva

            
            if indice_ciclo_etichette != self.label_counter:
                indice_ciclo_etichette += 1
                # Se lo spazio verticale si esaurisce, aggiungi una nuova pagina e resetta le coordinate
                if y + label_height > page_height - margin_y:
                    pdf.add_page()
                    x = margin_x
                    y = margin_y

        # Salva il PDF
        pdf.output(pdf_output)
        
        # Invio su FTP
        self.send_to_ftp(pdf_output)
        
        self.status_label.text = f"Etichette salvate e inviate su FTP come {filename}_{timestamp}.pdf."
        
        # Resetta il contatore delle etichette dopo aver stampato
        self.reset_counter()

        self.labels = []  # Resetta la lista delle etichette
        

    def print_labels(self, instance):
        if not self.labels:
            self.status_label.text = "Nessuna etichetta da stampare."
            return
        
        self.show_filename_popup()

        # # Percorso di salvataggio del PDF
        # timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        # output_dir = os.path.join(os.getcwd(), "tmp")
        # pdf_output = os.path.join(os.getcwd(), output_dir, f"labels_output_{timestamp}.pdf")
        
        # # Crea la cartella se non esiste
        # os.makedirs(output_dir, exist_ok=True)
        
        # # Configurazione della pagina e delle etichette
        # pdf = FPDF(orientation='P', unit='mm', format='A4')
        # label_width = 60  # Larghezza dell'etichetta in mm
        # label_height = 40  # Altezza dell'etichetta in mm
        # margin_x = 10  # Margine sinistro e destro in mm
        # margin_y = 10  # Margine superiore e inferiore in mm
        # labels_per_row = 3  # Numero di etichette per riga
        # page_width = 210  # Larghezza della pagina A4 in mm
        # page_height = 297  # Altezza della pagina A4 in mm

        # # Coordinate iniziali per la prima etichetta
        # x = margin_x
        # y = margin_y

        # # Aggiungi la prima pagina
        # pdf.add_page()

        # for label_path in self.labels:
        #     # Aggiungi l'etichetta alla posizione corrente
        #     pdf.image(label_path, x=x, y=y, w=label_width, h=label_height)

        #     # Aggiorna la posizione x per la prossima etichetta
        #     x += label_width

        #     # Se abbiamo raggiunto il limite di etichette per riga, resettiamo x e incrementiamo y
        #     if x + label_width > page_width - margin_x:
        #         x = margin_x  # Torna all'inizio della riga
        #         y += label_height  # Passa alla riga successiva

        #     # Se lo spazio verticale si esaurisce, aggiungi una nuova pagina e resetta le coordinate
        #     if y + label_height > page_height - margin_y:
        #         pdf.add_page()
        #         x = margin_x
        #         y = margin_y

        # # Salva il PDF
        # pdf.output(pdf_output)
        
        # # Invio su FTP
        # self.send_to_ftp(pdf_output)
        
        # self.status_label.text = "Etichette salvate e inviate su FTP."
        # self.labels = []  # Resetta la lista delle etichette
        
    def send_to_ftp(self, file_path):

        config = ConfigParser()
        config_file = get_asset_path('config.ini')
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