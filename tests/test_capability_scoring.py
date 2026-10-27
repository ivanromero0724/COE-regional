"""Deterministic tests for 24-question ordinal maturity rubric.

No personal data or external services required. The Argentina fixture codes are
used with public reference results from the initial 2026 sample fact sheets.
"""
import unittest
import json
from pathlib import Path
from scripts.generate_country_profiles import (
    read_first_sheet, HERE, DOMAINS, ITEM_RATINGS,
    score_by_index, scores, maturity_level, choice,
)

class MaturityRubricTests(unittest.TestCase):
    def test_unique_questions(self):
        cols=[j for _,indexes in DOMAINS for j in indexes]
        self.assertEqual([len(x) for _,x in DOMAINS], [5,6,5,5,3])
        self.assertEqual(len(cols),24)
        self.assertEqual(len(set(cols)),24)
        self.assertEqual(set(cols),set(ITEM_RATINGS))
        self.assertTrue(all(1 <= val <= 5 for item in ITEM_RATINGS.values() for val in item.values()))

    def test_reference_argentina(self):
        # The 24 reported answer categories from the 2026 reference profile.
        codes={29:'b',32:'a',33:'a',36:'b',37:'b',
               39:'a',43:'a',46:'b',47:'a',49:'d',50:'d',
               66:'b',68:'b',77:'c',78:'c',80:'a',
               105:'c',107:'d',108:'c',109:'a',110:'b',
               41:'c',42:'c',44:'e'}
        row=['']*167
        for idx,letter in codes.items():row[idx]=letter+'. selected answer'
        self.assertEqual([i[1] for i in scores(row)],[30,83,55,65,58])
        self.assertEqual([i[2] for i in scores(row)],[5,6,5,5,3])

    def test_all_original_reference_profiles(self):
        fixture = Path(__file__).with_name('reference_2026_scoring_cases.json')
        cases = json.loads(fixture.read_text())
        self.assertEqual(len(cases), 15)
        for profile in cases:
            with self.subTest(profile=profile['profile']):
                row = [''] * 167
                for idx, code in profile['answers'].items():
                    row[int(idx)] = code + '. survey response'
                self.assertEqual([v[1] for v in scores(row)], profile['expected'])

    def test_levels_and_missingness(self):
        for pts,level in [(0,'Initial'),(39,'Initial'),(40,'Developing'),
                          (59,'Developing'),(60,'Functional'),(79,'Functional'),
                          (80,'Advanced'),(100,'Advanced')]:
            self.assertEqual(maturity_level(pts),level)
        self.assertEqual(maturity_level(None),'Not scored')
        row=['']*167
        self.assertTrue(all(t[1] is None and t[2]==0 for t in scores(row)))
        row[29]='a. Inexistente'
        self.assertEqual(scores(row)[0][1],0)
        self.assertEqual(scores(row)[0][2],1)

    def test_current_workbook_schema(self):
        hdr=read_first_sheet(HERE/'data'/'Encuesta_OPS_2026_COEs.xlsx')[0]
        expected={29:'10.',32:'12.',33:'13.',36:'14.',37:'15.',
                  39:'16.',43:'20.',46:'22.',47:'23.',49:'24.',50:'25.',
                  66:'28.',68:'30.',77:'32.',78:'33.',80:'34.',
                  105:'38.',107:'39.',108:'40.',109:'41.',110:'42.',
                  41:'18.',42:'19.',44:'21.'}
        self.assertEqual(len(hdr),167)
        for idx,question in expected.items():
            self.assertTrue(str(hdr[idx]).startswith(question),f'Column {idx} changed: {hdr[idx]}')

if __name__=='__main__':unittest.main()