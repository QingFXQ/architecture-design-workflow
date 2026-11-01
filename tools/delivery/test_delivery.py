"""Behavioral fixtures: real PDFs, version pollution, missing drawings and print geometry."""
from pathlib import Path
import tempfile
import unittest
from check_delivery import validate

try:
    import fitz
except ImportError:
    fitz = None


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='arch-delivery-')
        self.root = Path(self.tmp.name)
        (self.root/'plan.png').write_bytes(b'independent fixture; image decoding is not asserted')
        self.manifest = {
            'project': {'current_revisions': {'design':'D2'}},
            'brief': {'board_count':1,'paper_mm':[594,841],'required_assets':['P1']},
            'assets': [{'id':'P1','kind':'plan','title':'首层平面图','file':'plan.png','scale':200,
                        'model_width_m':40,'source_revisions':{'design':'D2'},'visual_reviewed':True}],
            'boards': [{'id':'B1','file':'board.pdf','width_mm':594,'height_mm':841,
                        'placements':[{'asset':'P1','x_mm':10,'y_mm':20,'width_mm':200,'height_mm':300}],
                        'visual_review':{'overview':True,'details':True}}]
        }
        if fitz:
            self.pdf(594,841)

    def tearDown(self):
        self.tmp.cleanup()

    def pdf(self,w,h,pages=1):
        doc=fitz.open()
        for _ in range(pages):
            p=doc.new_page(width=w*72/25.4,height=h*72/25.4)
            p.insert_text((40,50),'Board fixture',fontsize=12)
        doc.save(self.root/'board.pdf');doc.close()

    def codes(self,data=None):
        return {i['code'] for i in validate(data or self.manifest,self.root) if i['level']=='error'}

    @unittest.skipUnless(fitz,'PDF integration needs existing PyMuPDF')
    def test_real_single_a1_and_consistent_scale(self):
        self.assertEqual(self.codes(),set())

    @unittest.skipUnless(fitz,'PDF integration needs existing PyMuPDF')
    def test_actual_landscape_pdf_does_not_pass_portrait_declaration(self):
        self.pdf(841,594)
        self.assertIn('PAPER_SIZE',self.codes())

    @unittest.skipUnless(fitz,'PDF integration needs existing PyMuPDF')
    def test_combined_two_page_pdf_is_not_one_board(self):
        self.pdf(594,841,pages=2)
        self.assertIn('BOARD_PAGE_COUNT',self.codes())

    def test_scaled_drawing_cannot_keep_old_label(self):
        self.manifest['boards'][0]['placements'][0]['width_mm']=100
        self.assertIn('PLACED_SCALE',self.codes())

    def test_stale_floor_contaminates_downstream_analysis(self):
        self.manifest['assets'][0]['source_revisions']['design']='D1'
        for key,dep in [('AX','P1'),('RENDER','AX')]:
            self.manifest['assets'].append({'id':key,'kind':'analysis','file':'plan.png','depends_on':[dep]})
        issues=validate(self.manifest,self.root)
        self.assertEqual({i['target'] for i in issues if i['code']=='STALE_DEPENDENCY'},{'AX','RENDER'})

    def test_required_basement_cannot_be_omitted_from_board(self):
        self.manifest['boards'][0]['placements']=[]
        self.assertIn('REQUIRED_NOT_PLACED',self.codes())

    def test_missing_export_file_cannot_count_as_delivered(self):
        (self.root/'plan.png').unlink()
        self.assertIn('MISSING_ASSET',self.codes())

    def test_empty_export_cannot_count_as_delivered(self):
        (self.root/'plan.png').write_bytes(b'')
        self.assertIn('EMPTY_ASSET',self.codes())

    def test_small_text_after_layout_remains_visible_warning(self):
        self.manifest['print_profile']={'min_text_height_mm':2.5}
        self.manifest['boards'][0]['placements'][0]['final_annotation_height_mm']=1.4
        self.assertIn('SMALL_DRAWING_TEXT',{i['code'] for i in validate(self.manifest,self.root)})


if __name__=='__main__':
    unittest.main()
