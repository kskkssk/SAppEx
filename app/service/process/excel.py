import pandas as pd


def process_excel(query, df):

    filename = f'{query}.xlsx'

    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        df.replace(to_replace=["None", ""],
                       value="-", inplace=True)
        df_all = df.copy()
        worksheet1 = writer.sheets['All']

        format_plus = writer.book.add_format({'bg_color': '#C6EFCE'})  # Зеленый
        format_minus = writer.book.add_format({'bg_color': '#FFC7CE'})  # Красный

        for row in range(1, len(df_all) + 1):  # Начинаем с 1, чтобы пропустить заголовок в Excel
            for col in range(len(df_all.columns)):
                cell_value = df_all.iat[row - 1, col] #значение из df
                if cell_value == '-':
                    worksheet1.write(row, col, '-', format_minus)  # Минус (красный). row в Excel с 1
                else:
                    worksheet1.write(row, col, '+', format_plus)  # Плюс (зеленый)

        worksheet2 = writer.sheets['Abstracts']
        df_abstract = df[['doi', 'abstract']].copy()
        df_abstract.to_excel(writer, sheet_name='Abstracts', index=False)
        for row in range(1, len(df_abstract) + 1):
            for col in range(len(df_abstract.columns)):
                cell_value = df_abstract.iat[row - 1, col]
                if cell_value == "-":
                    worksheet2.write(row, col, "-", format_minus)

        worksheet3 = writer.sheets['Keywords']
        df_keywords = df[['doi', 'keywords']].copy()
        df_keywords.to_excel(writer, sheet_name='Keywords', index=False)
        for row in range(1, len(df_keywords) + 1):
            for col in range(len(df_keywords.columns)):
                cell_value = df_keywords.iat[row - 1, col]
                if cell_value == "-":
                    worksheet3.write(row, col, "-", format_minus)

        worksheet4 = writer.sheets['References']
        df_references = df[['doi', 'references']].copy()
        df_references.to_excel(writer, sheet_name='References', index=False)
        for row in range(1, len(df_references) + 1):
            for col in range(len(df_references.columns)):
                cell_value = df_references.iat[row - 1, col]
                if cell_value == "-":
                    worksheet4.write(row, col, "-", format_minus)
        '''
        worksheet4 = writer.sheets['Introductions']
        df_keywords = df[['doi', 'keywords']].copy()
        df_keywords.to_excel(writer, sheet_name='Keywords', index=False)
        for row in range(1, len(df_keywords) + 1):
            for col in range(len(df_keywords.columns)):
                cell_value = df_keywords.iat[row - 1, col]
                if cell_value == "-":
                    worksheet4.write(row, col, "-", format_minus)
                    
        worksheet5 = writer.sheets['Materials and methods']
        df_keywords = df[['doi', 'keywords']].copy()
        df_keywords.to_excel(writer, sheet_name='Keywords', index=False)
        for row in range(1, len(df_keywords) + 1):
            for col in range(len(df_keywords.columns)):
                cell_value = df_keywords.iat[row - 1, col]
                if cell_value == "-":
                    worksheet5.write(row, col, "-", format_minus)
                    
        worksheet6 = writer.sheets['Results']
        df_results = df[['doi', 'results']].copy()
        df_results.to_excel(writer, sheet_name='Results', index=False)
        for row in range(1, len(df_results) + 1):
            for col in range(len(df_results.columns)):
                cell_value = df_results.iat[row - 1, col]
                if cell_value == "-":
                    worksheet6.write(row, col, "-", format_minus)
                    
        worksheet7 = writer.sheets['Conclusion']
        df_conclusion = df[['doi', 'conclusion']].copy()
        df_conclusion.to_excel(writer, sheet_name='Conclusion', index=False)
        for row in range(1, len(df_conclusion + 1)):
            for col in range(len(df_conclusion.columns)):
                cell_value = df_conclusion.iat[row - 1, col]
                if cell_value == "-":
                    worksheet7.write(row, col, "-", format_minus)
                    
        worksheet8 = writer.sheets['Acknowledgements']
        df_acknowledgements = df[['doi', 'acknowledgements']].copy()
        df_acknowledgements.to_excel(writer, sheet_name='Acknowledgements', index=False)
        for row in range(1, len(df_acknowledgements) + 1):
            for col in range(len(df_acknowledgements.columns)):
                cell_value = df_acknowledgements.iat[row - 1, col]
                if cell_value == "-":
                    worksheet8.write(row, col, "-", format_minus)
        '''
