import unittest
from workspace import Workspace, valid_geometry

class FakeWindow:
    def __init__(self):
        self.alive = True
        self.raised = 0
        self.size = '850x600+20+20'
    def winfo_exists(self): return self.alive
    def deiconify(self): pass
    def lift(self): self.raised += 1
    def focus_set(self): pass
    def geometry(self, value=None):
        if value is not None: self.size = value
        return self.size
    def protocol(self, *args): pass
    def destroy(self): self.alive = False

class WorkspaceTests(unittest.TestCase):
    def test_geometry_validation(self):
        self.assertTrue(valid_geometry('950x620+100+50'))
        self.assertTrue(valid_geometry('950x620-100+50'))
        for value in ('', 'bad', '10x20+0+0', '900x600', None):
            self.assertFalse(valid_geometry(value))
    def test_focus_existing_window(self):
        manager = Workspace(None)
        created = []
        def factory():
            window = FakeWindow(); created.append(window); return window
        self.assertIs(manager.open('Piano Roll', factory), manager.open('Piano Roll', factory))
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].raised, 1)
    def test_close_remembers_geometry(self):
        manager = Workspace(None, {'Piano Roll': '950x620+100+50'})
        window = manager.open('Piano Roll', FakeWindow)
        self.assertEqual(window.geometry(), '950x620+100+50')
        manager.close('Piano Roll')
        self.assertFalse(window.alive)
        self.assertEqual(manager.geometry['Piano Roll'], '950x620+100+50')
