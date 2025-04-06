from unittest.mock import inplace

import pandas as pd
import os

def process_excel(query, df, auth_counter, ref_counter):
    output_folder = 'results'
    os.makedirs(output_folder, exist_ok=True)

    filename = os.path.join(output_folder, f'{query}.xlsx')
    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        df.replace(to_replace=["None", "", None, "N/A"],
                       value="-", inplace=True)
        df_all = df.copy()
        df_all.drop(['methods_check'], axis=1, inplace=True)
        worksheet1 = writer.book.add_worksheet('All')

        format_plus = writer.book.add_format({'bg_color': '#C6EFCE'})  # Зеленый
        format_minus = writer.book.add_format({'bg_color': '#FFC7CE'})  # Красный
        format_header = writer.book.add_format({'bold': True})

        for col_num, value in enumerate(df_all.columns):
            worksheet1.write(0, col_num, value, format_header)

        for row in range(1, len(df_all) + 1):  # Начинаем с 1, чтобы пропустить заголовок в Excel
            for col in range(len(df_all.columns)):
                cell_value = df_all.iat[row - 1, col] #значение из df
                if col > 1:
                    if cell_value == '-':
                        worksheet1.write(row, col, '-', format_minus)  # Минус (красный). row в Excel с 1
                    else:
                        worksheet1.write(row, col, '+', format_plus)  # Плюс (зеленый)
                else:
                    if cell_value == '-':
                        worksheet1.write(row, col, '-', format_minus)  # Минус (красный). row в Excel с 1
                    else:
                        worksheet1.write(row, col, cell_value)

        worksheet2 = writer.book.add_worksheet('Abstract')
        df_abstract = df[['title', 'doi', 'abstract']].copy()
        for col_num, value in enumerate(df_abstract.columns):
            worksheet2.write(0, col_num, value, format_header)
        df_abstract.to_excel(writer, sheet_name='Abstract', index=False)
        for row in range(1, len(df_abstract) + 1):
            for col in range(len(df_abstract.columns)):
                cell_value = df_abstract.iat[row - 1, col]
                if cell_value == "-":
                    worksheet2.write(row, col, "-", format_minus)

        worksheet3 = writer.book.add_worksheet('Keywords')
        df_keywords = df[['title', 'doi', 'keywords']].copy()
        for col_num, value in enumerate(df_keywords.columns):
            worksheet3.write(0, col_num, value, format_header)
        df_keywords.to_excel(writer, sheet_name='Keywords', index=False)
        for row in range(1, len(df_keywords) + 1):
            for col in range(len(df_keywords.columns)):
                cell_value = df_keywords.iat[row - 1, col]
                if cell_value == "-":
                    worksheet3.write(row, col, "-", format_minus)

        worksheet4 = writer.book.add_worksheet('Introduction')
        df_introduction = df[['title', 'doi', 'introduction']].copy()
        for col_num, value in enumerate(df_introduction.columns):
            worksheet4.write(0, col_num, value, format_header)
        df_introduction.to_excel(writer, sheet_name='Introduction', index=False)
        for row in range(1, len(df_introduction) + 1):
            for col in range(len(df_introduction.columns)):
                cell_value = df_introduction.iat[row - 1, col]
                if cell_value == "-":
                    worksheet4.write(row, col, "-", format_minus)

        worksheet5 = writer.book.add_worksheet('References')
        df_references = df[['title', 'doi', 'references']].copy()
        for col_num, value in enumerate(df_references.columns):
            worksheet5.write(0, col_num, value, format_header)
        df_references.to_excel(writer, sheet_name='References', index=False)
        for row in range(1, len(df_references) + 1):
            for col in range(len(df_references.columns)):
                cell_value = df_references.iat[row - 1, col]
                if cell_value == "-":
                    worksheet5.write(row, col, "-", format_minus)

        worksheet6 = writer.book.add_worksheet('Methods')
        df_methods = df[['title', 'doi', 'methods']].copy()
        for col_num, value in enumerate(df_methods.columns):
            worksheet6.write(0, col_num, value, format_header)
        df_methods.to_excel(writer, sheet_name='Methods', index=False)
        for row in range(1, len(df_methods) + 1):
            for col in range(len(df_methods.columns)):
                cell_value = df_methods.iat[row - 1, col]
                if cell_value == "-":
                    worksheet6.write(row, col, "-", format_minus)

        worksheet7 = writer.book.add_worksheet('Discussion')
        df_discussion = df[['title', 'doi', 'discussion']].copy()
        for col_num, value in enumerate(df_discussion.columns):
            worksheet7.write(0, col_num, value, format_header)
        df_discussion.to_excel(writer, sheet_name='Discussion', index=False)
        for row in range(1, len(df_discussion) + 1):
            for col in range(len(df_discussion.columns)):
                cell_value = df_discussion.iat[row - 1, col]
                if cell_value == "-":
                    worksheet7.write(row, col, "-", format_minus)

        worksheet8 = writer.book.add_worksheet('Conclusion')
        df_conclusion = df[['title', 'doi', 'conclusion']].copy()
        for col_num, value in enumerate(df_conclusion.columns):
            worksheet8.write(0, col_num, value, format_header)
        df_conclusion.to_excel(writer, sheet_name='Conclusion', index=False)
        for row in range(1, len(df_conclusion) + 1):
            for col in range(len(df_conclusion.columns)):
                cell_value = df_conclusion.iat[row - 1, col]
                if cell_value == "-":
                    worksheet8.write(row, col, "-", format_minus)

        worksheet9 = writer.book.add_worksheet('Results')
        df_results = df[['title', 'doi', 'results']].copy()
        for col_num, value in enumerate(df_results.columns):
            worksheet9.write(0, col_num, value, format_header)
        df_results.to_excel(writer, sheet_name='Results', index=False)
        for row in range(1, len(df_results) + 1):
            for col in range(len(df_results.columns)):
                cell_value = df_results.iat[row - 1, col]
                if cell_value == "-":
                    worksheet9.write(row, col, "-", format_minus)

        worksheet10 = writer.book.add_worksheet('Full')
        df_texts = df[['title', 'doi', 'full']].copy()
        for col_num, value in enumerate(df_texts.columns):
            worksheet10.write(0, col_num, value, format_header)
        df_texts.to_excel(writer, sheet_name='Full', index=False)
        for row in range(1, len(df_texts) + 1):
            for col in range(len(df_texts.columns)):
                cell_value = df_texts.iat[row - 1, col]
                if cell_value == "-":
                    worksheet10.write(row, col, "-", format_minus)

        worksheet11 = writer.book.add_worksheet('Methods check')
        df_check = df[['title', 'doi', 'methods_check']].copy()
        for col_num, value in enumerate(df_check.columns):
            worksheet11.write(0, col_num, value, format_header)
        df_check.to_excel(writer, sheet_name='Methods check', index=False)
        for row in range(1, len(df_check) + 1):
            for col in range(len(df_check.columns)):
                cell_value = df_check.iat[row - 1, col]
                if cell_value == "-":
                    worksheet11.write(row, col, "-", format_minus)

        worksheet12 = writer.book.add_worksheet('Authors references')
        df_counter = ref_counter.copy()
        for col_num, value in enumerate(df_counter.columns):
            worksheet12.write(0, col_num, value, format_header)
        df_counter.to_excel(writer, sheet_name='Authors references', index=False)
        for row in range(1, len(df_counter) + 1):
            for col in range(len(df_counter.columns)):
                cell_value = df_counter.iat[row - 1, col]
                if cell_value == "-":
                    worksheet12.write(row, col, "-", format_minus)

        worksheet13 = writer.book.add_worksheet('Authors')
        df_authors = df[['title', 'doi', 'authors']].copy()
        for col_num, value in enumerate(df_authors.columns):
            worksheet13.write(0, col_num, value, format_header)
        df_authors.to_excel(writer, sheet_name='Authors', index=False)
        for row in range(1, len(df_authors) + 1):
            for col in range(len(df_authors.columns)):
                cell_value = df_authors.iat[row - 1, col]
                if cell_value == "-":
                    worksheet13.write(row, col, "-", format_minus)

        worksheet14 = writer.book.add_worksheet('Authors papers')
        df_counter = auth_counter.copy()
        for col_num, value in enumerate(df_counter.columns):
            worksheet14.write(0, col_num, value, format_header)
        df_counter.to_excel(writer, sheet_name='Authors papers', index=False)
        for row in range(1, len(df_counter) + 1):
            for col in range(len(df_counter.columns)):
                cell_value = df_counter.iat[row - 1, col]
                if cell_value == "-":
                    worksheet14.write(row, col, "-", format_minus)

    return filename