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
        res = super()._read_file(options)
        return res


class AccountJournalImportInherit(models.Model):
    _inherit = "account.journal"

    def _get_bank_statements_available_import_formats(self):
        rslt = super()._get_bank_statements_available_import_formats()
        rslt.append('XML')
        return rslt

    def _check_xml(self, attachment):
        try:
            ET.fromstring(attachment.raw or b'')
            return True
        except ET.ParseError:
            return False

    def _parse_bank_statement_file(self, attachment):
        if not self._check_xml(attachment):
            return super()._parse_bank_statement_file(attachment)

        file_content = base64.b64decode(attachment.datas)
        root = ET.fromstring(file_content)
        vals_bank_statement = []
        account_lst = set()
        currency_lst = set()
        zaglavlje = root.find('.//Zaglavlje')
        date_str = zaglavlje.get('DatumIzvoda')
        date = datetime.strptime(date_str, '%d.%m.%Y').strftime('%Y-%m-%d')

        balance_start = 0.0
        total_amt = 0.0
        transactions = []

        for stavka in root.findall('.//Stavke'):
            account_number = stavka.get('BrojRacunaPrimaocaPosiljaoca')
            currency = "RSD"
            account_user = stavka.get('NalogKorisnik')
            memo = stavka.get('Opis')
            trans_id = stavka.get('Referenca')

            duguje = float(stavka.get('Duguje', '0'))
            potrazuje = float(stavka.get('Potrazuje', '0'))

            if duguje == 0 and potrazuje > 0:
                amount = potrazuje
            else:
                amount = -duguje

            partner_bank = self.env['res.partner.bank'].search([('partner_id.name', '=', account_user)], limit=1)
            vals_line = {
                'date': date,
                'payment_ref': account_user + (memo and ': ' + memo or ''),
                'ref': trans_id,
                'amount': amount,
                'unique_import_id': trans_id,
                'account_number': partner_bank.acc_number if partner_bank else '',
                'partner_id': partner_bank.partner_id.id if partner_bank else None,
                'sequence': len(transactions) + 1,
            }

            transactions.append(vals_line)
            total_amt += amount

        vals_bank_statement.append({
            'transactions': transactions,
        })

        return currency_lst, account_lst, vals_bank_statement
