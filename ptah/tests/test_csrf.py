import transaction
from datetime import timedelta
from memphis import config

from base import Base


class TestCsrf(Base):

    def tearDown(self):
        config.cleanup_system(self.__class__.__module__)
        super(TestCsrf, self).tearDown()

    def test_csrf_service(self):
        import ptah
        from ptah.util import CSRFService

        self._init_memphis()

        csrf = CSRFService()
        t = csrf.generate('test')

        self.assertEqual(csrf.get(t), 'test')
        self.assertEqual(csrf.generate('test'), t)

        csrf.remove(t)
        self.assertEqual(csrf.get(t), None)

        t2 = csrf.generate('test')
        self.assertTrue(t != t2)
