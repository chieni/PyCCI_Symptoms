from main_application import *
from menu_bar import *
import tkFont
import tkFileDialog
import Tkinter as tk

def main(): 
	title = "Heart Failure Symptoms"
	textbox_labels = ['Negative Symptom', 'Negation', 'Positive Symptom', 'Positive Modifier', 'Neutral Symptom', 'Ambiguous']
	textbox_label_to_key_dict = {'Negative Symptom': 's', 'Negation': 'a', 'Positive Symptom': 'f', 'Positive Modifier': 'd', 'Neutral Symptom': 'g', 'Ambiguous': 'e'}
	labels_to_codes = {'Negative Symptom': 'NSY', 'Negation':'NEG', 'Positive Symptom': 'PSY', 'Positive Modifier':'PMO', 'Neutral Symptom': 'NEU', 'Ambiguous': 'AMB'}
	reviewer_labels = ['NSY', 'PSY', 'NEG', 'PMO', 'NEU', 'NMO','AMB']
	comment_boxes = []
	checkbox_labels = ["None"]
	text_config = {'keywords_fname': 'keywords.txt', 'text_key': 'TEXT', 'note_key': 'ROW_ID', 'patient_key': 'HADM_ID', 'category_key': 'CATEGORY', 'results_fname_suffix': 'Results.csv', 'review_fname': 'reviewed.csv'}
	root = tk.Tk()
	MainApplication(root, title, textbox_labels, checkbox_labels, comment_boxes, reviewer_labels, textbox_label_to_key_dict, labels_to_codes, text_config).pack(side="top", fill="both", expand=True)
	menubar = MenuBar(root)
	root.config(menu=menubar)
	root.mainloop()

if __name__ == '__main__':
    main()