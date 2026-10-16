import unittest
from import_sumulas import entry, source_url


class SumulasImportTests(unittest.TestCase):
    def test_statement_separated_from_commentary_and_footer_not_added(self):
        pages = [(1, [(50, 'Súmula Vinculante 13', True),
                       (80, 'Aplicação das Súmulas no STF', False),
                       (100, 'Fonte: página oficial do STF | Consulta em 16/10/2026', False),
                       (140, 'Enunciado de teste com conteúdo próprio preservado.', False),
                       (190, 'Precedentes Representativos', True),
                       (210, 'Comentário com citação da Súmula Vinculante 9 (cancelada).', False)],
                  'https://portal.stf.jus.br/jurisprudencia/sumariosumulas.asp?base=26&sumula=1185'),
                 (2, [(50, 'Continuação dos precedentes na página seguinte.', False)], None)]
        result = entry(13, 'Súmula Vinculante 13', pages)
        self.assertEqual(result['status'], 'as_provided')
        self.assertEqual(len(result['paragraphs']), 1)
        self.assertEqual(result['notes'][-1]['page'], 2)
        self.assertEqual(result['notes'][-1]['runs'][0]['text'], 'Continuação dos precedentes na página seguinte.')
        self.assertTrue(result['notes'][0]['heading'])
        pages[0][1][2] = (100, 'Fonte desconhecida', False)
        with self.assertRaises(ValueError):
            entry(13, 'Súmula Vinculante 13', pages)

    def test_source_links_require_stf_host_and_collection(self):
        for url in ['https://example.com/?base=26&sumula=1185',
                    'https://portal.stf.jus.br.evil.test/jurisprudencia/sumariosumulas.asp?base=26&sumula=1185',
                    'https://portal.stf.jus.br/jurisprudencia/sumariosumulas.asp?base=30&sumula=1185']:
            with self.assertRaises(ValueError):
                source_url([{'uri': url}])
        valid = 'https://portal.stf.jus.br/jurisprudencia/sumariosumulas.asp?base=26&sumula=1185'
        self.assertEqual(source_url([{'uri': valid}]), valid)


if __name__ == '__main__':
    unittest.main()
