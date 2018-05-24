import csv
from numpy import NaN, isnan, arange
import os
import pandas as pd
import re
import time
import tkFont
import tkFileDialog
import tkMessageBox
import Tkinter as tk


class AnnotationPanel(tk.Frame):
    def __init__(self, master, checkframe, textbox_labels, comment_boxes, checkbox_labels, textbox_labels_to_key_dict, labels_to_codes, text_config):
        self.master = master
        self.checkframe = checkframe
        self.textbox_labels = textbox_labels
        self.comment_boxes = comment_boxes
        self.checkbox_labels = checkbox_labels
        self.textbox_labels_to_key_dict = textbox_labels_to_key_dict
        self.labels_to_codes = labels_to_codes
        self.text_config = text_config
        tk.Frame.__init__(self, self.master)
        self.last_highlighted_char_index = None
        self.last_highlighted_text = None
        self.textfont = tkFont.Font(family='Helvetica', size=15)
        self.smallfont = tkFont.Font(family='Helvetica', size=12)
        
        self.textbox_labels_display_order = ['Positive Modifier', 'Positive Symptom', 'Negation', 'Negative Symptom', 'Neutral Symptom', 'Ambiguous']
        
        self.textboxes = {}
        self.textbox_to_checkbox = {}
        self.textbox_char_starts = {label: [] for label in self.textbox_labels}
        self.comments = {}
        self.indicator_values = {label: 0 for label in self.textbox_labels + self.checkbox_labels}
        self.create_annotation_items()

    ### Initialization of annotation panel widgets
    def create_annotation_items(self):
        '''
        Creates the checkbuttons and text entry box
        The part of the gui that covers annotations
        '''
        for item in self.textbox_labels_display_order:
            checkbox, checkbox_val = self.create_checkbox(item)
            self.create_textbox(item, checkbox, checkbox_val)
        for item in self.checkbox_labels:
            self.create_checkbox(item)

    def create_comment_box(self, label):
        original_text = label + " Comments"
        text_frame = tk.Frame(self.checkframe, borderwidth=1, relief="sunken")
        entry = tk.Text(wrap="word", background="white", 
                            borderwidth=0, highlightthickness=0, height=2)
        entry.insert(tk.END, original_text)
        vsb = tk.Scrollbar(orient="vertical", borderwidth=1,
                                command=entry.yview)
        entry.configure(yscrollcommand=vsb.set, font=self.smallfont, padx=3, pady=3)
        vsb.pack(in_=text_frame,side="right", fill="y", expand=False)
        entry.pack(in_=text_frame, side="left", fill="both", expand=True)
        text_frame.pack(anchor=tk.W, fill=tk.X, pady=5, padx=(0,5))
        entry.bind("<Button-1>", lambda event: self.clear_entry(event, entry, original_text))
        self.comments[label] = entry

    def create_checkbox(self, label):
        checkbox_val = tk.IntVar()
        checkbox_val.set(self.indicator_values[label])
        self.indicator_values[label] = checkbox_val
        checkbox_label = label
        if label in self.textbox_labels_to_key_dict:
            checkbox_label = label + " (" + self.textbox_labels_to_key_dict[label] + ") "

        checkbox = tk.Checkbutton(self.checkframe,
                        text=checkbox_label,
                        variable=checkbox_val,
                        onvalue=1,
                        offvalue=0,
                        height=1,
                        pady=5,
                        justify=tk.LEFT)
        checkbox.pack(anchor=tk.W)
        return checkbox, checkbox_val

    def create_textbox(self, label, checkbox, checkbox_val):
        y_padding = 5
        if label == 'Negative Symptom' or label == 'Positive Symptom' or label == 'Neutral Symptom':
            y_padding = 30
        original_text = label + " Text"
        text_frame = tk.Frame(self.checkframe, borderwidth=1, relief="sunken")
        entry = tk.Text(wrap="word", background="white", 
                            borderwidth=0, highlightthickness=0, height=2)
        entry.insert(tk.END, original_text)
        vsb = tk.Scrollbar(orient="vertical", borderwidth=1,
                                command=entry.yview)
        entry.configure(yscrollcommand=vsb.set, font=self.smallfont, padx=3, pady=3)
        vsb.pack(in_=text_frame,side="right", fill="y", expand=False)
        entry.pack(in_=text_frame, side="left", fill="both", expand=True)
        text_frame.pack(anchor=tk.W, fill=tk.X, pady=(0,y_padding))

        checkbox.bind("<Button-1>", lambda event: self.clear_entry_from_check(event, entry, checkbox_val, label))
        entry.bind("<BackSpace>", lambda event: self.handle_backspace(event, entry, checkbox, original_text, label))
        entry.bind("<Button-1>", lambda event: self.clear_entry(event, entry, original_text))
        entry.bind("<Command-v>", lambda event: self.on_paste(event, label, checkbox))
        self.textbox_to_checkbox[label] = checkbox
        self.textboxes[label] = entry

    def add_text_to_textbox(self, start, text, textbox_label):
        original_text = textbox_label + " Text"
        parts = []
        current_dist = 0
        entry = self.textboxes[textbox_label]
        self.clear_entry(None, entry, original_text)
        if len(text) > 0:
            self.textbox_to_checkbox[textbox_label].select()
        # If there are commas, split by comma and add each thing to char_starts
        if ',' in text:
            parts = text.split(',')
            for part in parts:
                # If stuff was already in the text box, add a comma
                if len(entry.get(1.0, 'end-1c').strip()) > 0:
                    entry.insert(tk.END, ", ")
                current_dist += re.search(r'\w', part).start()
                self.textbox_char_starts[textbox_label].append(start + current_dist)
                current_dist += len(part) + 1 - re.search(r'\w', part).start()
                entry.insert(tk.END, part)
        else:
            if len(entry.get(1.0, 'end-1c').strip()) > 0:
                entry.insert(tk.END, ", ")
            entry.insert(tk.END, text)
            alpha_start = re.search(r'\w', text).start()
            self.textbox_char_starts[textbox_label].append(start + alpha_start)

    def on_paste(self, event, label, checkbox):
        if len(event.char) > 0:
            checkbox.select()
        parts = []
        current_dist = 0
        # if there are commas, then split by comma and add each thing to char_starts
        if ',' in self.last_highlighted_text:
            parts = self.last_highlighted_text.split(',')
            for part in parts:
                current_dist += re.search(r'\w', part).start()
                self.textbox_char_starts[label].append(self.last_highlighted_char_index + current_dist)
                current_dist += len(part) + 1 - re.search(r'\w', part).start()
        else:
            self.textbox_char_starts[label].append(self.last_highlighted_char_index)

    def handle_backspace(self, event, entry, checkbox, original_text, label):
        if len(entry.get(1.0, 'end-1c')) < 2:
            checkbox.deselect()
            self.textbox_char_starts[label] = []

    def clear_entry(self, event, entry, original_text):
        if entry.get(1.0, 'end-1c') == original_text:
            entry.delete(1.0, tk.END)

    def clear_entry_from_check(self, event, entry, checkbox_val, label):
        if checkbox_val.get() == 1:
            entry.delete(1.0, tk.END)
            self.textbox_char_starts[label] = []
    
    ### Results file generation
    def save_annotations(self, data_df, row_index, results_df, is_comparison=False):
        '''
        save_annotations() is called every time "Next" or "Back" are pressed
        save_annotations() will create a results file if one does not exist if 
        an annotation is made
        save_annotations() will pass if no indicators are ticked
        save_annotations() will write to results file if any indicator is ticked

        data_df: original notes dataframe
        '''
        # If the file does not exist, create it and add the header
    
        data_labels = ['ROW_ID', 'TEXT', 'LABELLED_TEXT', 'START', 'LABEL', 'RELATED_TEXT', 'RELATED_START', 'RELATED_LABEL', 'NO_LABELS', 'STAMP']
        indicator_ints = [val.get() for val in self.indicator_values.values()]
        if sum(indicator_ints) != 0:
            new_results_df = self.generate_new_results_df(data_df, row_index, data_labels, is_comparison)
            if new_results_df is None:
                return None

            if results_df is not None:
                results_df = pd.concat([results_df, new_results_df], ignore_index=True)
                results_df = results_df[data_labels]
            else:
                results_df = new_results_df
            self.reset_buttons()

        self.textbox_char_starts = {label: [] for label in self.textbox_labels}
        return results_df

    def generate_new_results_df(self, data_df, row_index, data_labels, is_comparison):
        results_list = []
        negation = None
        modification = None
        n_modification = None
        labels = set()
        if self.indicator_values['None'].get() == 1:
            results_dict = {}
            results_dict['ROW_ID'] = data_df['ROW_ID'].iloc[row_index]
            results_dict['TEXT'] = data_df['TEXT'].iloc[row_index]
            results_dict['START'] = None
            results_dict['LABEL'] = None
            results_dict['RELATED_TEXT'] = None
            results_dict['RELATED_START'] = None
            results_dict['RELATED_LABEL'] = None
            results_dict['NO_LABELS'] = 1
            results_dict['STAMP'] = str(time.asctime(time.localtime(time.time())))
            results_list.append(results_dict)
        else:
            for textbox_column in self.textbox_labels:
                if self.indicator_values[textbox_column].get() == 1:
                    labels.add(textbox_column)
                    annotation_text = self.textboxes[textbox_column].get(1.0, 'end-1c').strip()
                    if len(annotation_text) < 1:
                        tkMessageBox.showerror("Error", "No text in textbox")
                        return None
                    char_starts = self.textbox_char_starts[textbox_column]
                    annotation_parts = [a.strip() for a in annotation_text.split(',')]
                    if len(char_starts) != len(annotation_parts):
                        tkMessageBox.showerror("Error", "Some annotation was not copied directly from text.")
                        return None
                    if textbox_column == 'Negation' or textbox_column == 'Positive Modifier':
                        if len(annotation_parts) != 1:
                            tkMessageBox.showerror("Error", "Negation or modification can only have one entity")
                            return None
                    if textbox_column == 'Negation':
                        if 'Negative Symptom' not in labels:
                            tkMessageBox.showerror("Error", "Negation must be associated with Negative Symptom")
                            return None 
                    if textbox_column == 'Positive Modifier':
                        if 'Positive Symptom' not in labels:
                            tkMessageBox.showerror("Error", "Positive Modifier must be associated with Positive Symptom")
                            return None 

                    for part, char_start in zip(annotation_parts, char_starts):
                        results_dict = {}
                        results_dict['ROW_ID'] = data_df['ROW_ID'].iloc[row_index]
                        results_dict['TEXT'] = data_df['TEXT'].iloc[row_index]
            
                        # Check that the text is actually in the clinical note (prevent copy errors)
                        start_index = None
                        start_index = results_dict['TEXT'].find(part)

                        if start_index == -1:
                            tkMessageBox.showerror("Error", "Text in " + textbox_column + " textbox is not found in original note.")
                            return None

                        results_dict['LABELLED_TEXT'] = part.strip()
                        results_dict['START'] = int(char_start)
                        results_dict['LABEL'] = self.labels_to_codes[textbox_column]
                        results_dict['RELATED_TEXT'] = None
                        results_dict['RELATED_START'] = None
                        results_dict['RELATED_LABEL'] = None
                        results_dict['NO_LABELS'] = 0
                        results_dict['STAMP'] = str(time.asctime(time.localtime(time.time())))
                        if textbox_column == 'Negation':
                            negation = results_dict
                        if textbox_column == 'Positive Modifier':
                            modification = results_dict
                        results_list.append(results_dict)


        # Now go through and check if there are Negations or Modifications related to symbols
        if negation is not None:
            # If negation exists, connect it with all negative symptoms
            for i in range(len(results_list)):
                if results_list[i]['LABEL'] == 'NSY':
                    results_list[i]['RELATED_TEXT'] = negation['LABELLED_TEXT']
                    results_list[i]['RELATED_START'] = int(negation['START'])
                    results_list[i]['RELATED_LABEL'] = negation['LABEL']

        if modification is not None:
            # If modification exists, connect it with all positive symptoms
            for i in range(len(results_list)):
                if results_list[i]['LABEL'] == 'PSY':
                    results_list[i]['RELATED_TEXT'] = modification['LABELLED_TEXT']
                    results_list[i]['RELATED_START'] = int(modification['START'])
                    results_list[i]['RELATED_LABEL'] = modification['LABEL']


        results_df = pd.DataFrame(results_list, columns=data_labels, index=arange(len(results_list)))
        return results_df

    def save_review_annotations(self, review_df, row_id):
        data_labels = [self.text_config['note_key'], self.text_config['text_key'], 'LABELLED_TEXT', 'START', 'LABELS', 'RELATED_TEXTS', 'RELATED_STARTS', 'RELATED_LABELS', 'ANNOTATORS', 'REVIEWER_LABELS']
        indicator_ints = [val.get() for val in self.indicator_values.values()]
        if sum(indicator_ints) != 0:
            clin_text = review_df[review_df[self.text_config['note_key']] == row_id][self.text_config['text_key']].values.tolist()[0]
            new_results_df = self.generate_new_review_df(data_labels, row_id, clin_text)
            if new_results_df is None:
                return None
            else:
                review_df = pd.concat([review_df, new_results_df], ignore_index=True)
                review_df = review_df[data_labels]
            self.reset_buttons()

        self.textbox_char_starts = {label: [] for label in self.textbox_labels}
        return review_df

    def generate_new_review_df(self, data_labels, row_id, clin_text):
        results_list = []
        negation = None
        modification = None
        n_modification = None
        labels = set()
        if self.indicator_values['None'].get() == 0:
            for textbox_column in self.textbox_labels:
                if self.indicator_values[textbox_column].get() == 1:
                    labels.add(textbox_column)
                    annotation_text = self.textboxes[textbox_column].get(1.0, 'end-1c').strip()
                    if len(annotation_text) < 1:
                        tkMessageBox.showerror("Error", "No text in textbox")
                        return None
                    char_starts = self.textbox_char_starts[textbox_column]
                    annotation_parts = [a.strip() for a in annotation_text.split(',')]
                    if len(char_starts) != len(annotation_parts):
                        tkMessageBox.showerror("Error", "Some annotation was not copied directly from text.")
                        return None
                    if textbox_column == 'Negation' or textbox_column == 'Positive Modifier':
                        if len(annotation_parts) != 1:
                            tkMessageBox.showerror("Error", "Negation or modification can only have one entity")
                            return None
                    if textbox_column == 'Negation':
                        if 'Negative Symptom' not in labels:
                            tkMessageBox.showerror("Error", "Negation must be associated with Negative Symptom")
                            return None 
                    if textbox_column == 'Positive Modifier':
                        if 'Positive Symptom' not in labels:
                            tkMessageBox.showerror("Error", "Positive Modifier must be associated with Positive Symptom")
                            return None 


                    for part, char_start in zip(annotation_parts, char_starts):
                        results_dict = {}
                        results_dict['ROW_ID'] = row_id
                        results_dict['TEXT'] = clin_text
                        results_dict['REVIEWER_LABELS'] = [self.labels_to_codes[textbox_column]]
                        # Check that the text is actually in the clinical note (prevent copy errors)
                        start_index = results_dict['TEXT'].find(annotation_text)

                        if start_index < 0:
                            tkMessageBox.showerror("Error", "Text in " + textbox_column + " textbox is not found in original note.")
                            return None

                        results_dict['LABELLED_TEXT'] = annotation_text.strip()
                        results_dict['START'] = int(char_start)
                        results_dict['LABELS'] = None
                        results_dict['RELATED_TEXTS'] = None
                        results_dict['RELATED_STARTS'] = None
                        results_dict['RELATED_LABELS'] = None
                        if textbox_column == 'Negation':
                            negation = results_dict
                        if textbox_column == 'Positive Modifier':
                            modification = results_dict
                        results_list.append(results_dict)

        # Now go through and check if there are Negations or Modifications related to symbols
        if negation is not None:
            # If negation exists, connect it with all negative symptoms
            for i in range(len(results_list)):
                if 'NSY' in results_list[i]['REVIEWER_LABELS']:
                    results_list[i]['RELATED_TEXTS'] = negation['LABELLED_TEXT']
                    results_list[i]['RELATED_STARTS'] = int(negation['START'])
                    results_list[i]['RELATED_LABELS'] = negation['REVIEWER_LABELS']

        if modification is not None:
            # If modification exists, connect it with all positive symptoms
            for i in range(len(results_list)):
                if 'PSY' in results_list[i]['REVIEWER_LABELS']:
                    results_list[i]['RELATED_TEXTS'] = modification['LABELLED_TEXT']
                    results_list[i]['RELATED_STARTS'] = int(modification['START'])
                    results_list[i]['RELATED_LABELS'] = modification['REVIEWER_LABELS']

        results_df = pd.DataFrame(results_list, columns=data_labels, index=arange(len(results_list)))
        return results_df

    def reset_buttons(self):
        for key, entry in self.textboxes.iteritems():
            entry.delete(1.0,tk.END)
            entry.insert(tk.END, key + " Text")
        for key, entry in self.comments.iteritems():
            entry.delete(1.0,tk.END)
            entry.insert(tk.END, key + " Comments")
        for machine in self.textbox_labels + self.checkbox_labels:
            self.indicator_values[machine].set(0)
