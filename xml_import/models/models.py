# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons.base_import.models.base_import import FILE_TYPE_DICT
import xml.etree.ElementTree as ET
import base64
from datetime import datetime






class baseimportInherit(models.TransientModel):
    _inherit = 'base_import.import'

    def _read_file(self, options):
        FILE_TYPE_DICT['text/xml'] = ('xml', ET, None)
        (file_extension, handler, req) = FILE_TYPE_DICT.get(self.file_type, (None, None, None))
        # if handler:
        #     try:
        #         if file_extension == 'xml':
        #             return self._read_xml(options)
        #     except Exception as e:
        #         # Handle exceptions
        #         pass
        res =  super()._read_file(options)
        return(res)


class AccountJournalImportInherit(models.Model):

    _inherit = "account.journal"

    def _get_bank_statements_available_import_formats(self):
        rslt = super()._get_bank_statements_available_import_formats()
        rslt.append('XML')
        return rslt
    # def _check_file_format(self, filename):
    #     return filename and filename.lower().strip().endswith(('.csv', '.xls', '.xlsx','.xml'))

    def _check_xml(self, attachment):
        try:
            # Try to parse the XML to check if it's valid
            ET.fromstring(attachment.raw or b'')
            return True
        except ET.ParseError:
            return False

    def _parse_bank_statement_file(self, attachment):

        if not self._check_xml(attachment):
            return super()._parse_bank_statement_file(attachment)
        # Ensure we have the correct file content
        file_content = base64.b64decode(attachment.datas)

        # Parse the XML content
        root = ET.fromstring(file_content)
        vals_bank_statement = []
        account_lst = set()
        currency_lst = set()
        zaglavlje = root.find('.//Zaglavlje')
        date_str = zaglavlje.get('DatumIzvoda')

        # Parsing the date
        date = datetime.strptime(date_str, '%d.%m.%Y').strftime('%Y-%m-%d')

        for stavka in root.findall('.//Stavke'):
            # Extracting the necessary fields from the XML
            account_number = stavka.get('BrojRacunaPrimaocaPosiljaoca')
            currency = "RSD"  # Assuming the currency is RSD as per the provided XML snippet

            account_user = stavka.get('NalogKorisnik')
            memo = stavka.get('Opis')
            trans_id = stavka.get('Referenca')
            amount = float(stavka.get('Duguje', '0'))
            partner_bank = self.env['res.partner.bank'].search([('partner_id.name', '=', account_user)], limit=1)
            vals_line = {
                'date': date,
                'payment_ref': account_user + (memo and ': ' + memo or ''),
                'ref': trans_id,
                'amount': -amount,
                'unique_import_id': trans_id,
                'account_number': partner_bank.acc_number if partner_bank else '',
                'partner_id': partner_bank.partner_id.id if partner_bank else None,
                'sequence': len(vals_bank_statement) + 1,
            }

            transactions = [vals_line]
            total_amt = amount


            balance_start = 0.0
            balance_end_real = total_amt

            vals_bank_statement.append({
                'transactions': transactions,
                'balance_start': balance_start,
                'balance_end_real': balance_end_real,
            })

        #     account_lst.add(account_number)
        #     currency_lst.add(currency)
        #
        # if account_lst and len(account_lst) == 1:
        #     account_lst = account_lst.pop()
        #     currency_lst = currency_lst.pop()
        # else:
        account_lst = None
        currency_lst = None

        return currency_lst, account_lst, vals_bank_statement

