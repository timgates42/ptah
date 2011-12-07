import unittest


class StopExceptionTesting(unittest.TestCase):

    def test_api_stopexception_msg(self):
        from ptah import config

        err = config.StopException('Error message')

        self.assertEqual(str(err), '\nError message')
        self.assertEqual(err.print_tb(), 'Error message')

    def test_api_stopexception_exc(self):
        from ptah import config

        s_err = None
        try:
            raise ValueError('err')
        except Exception as exc:
            s_err = config.StopException(exc)

        self.assertIn("raise ValueError('err')", s_err.print_tb())


class LoadpackageTesting(unittest.TestCase):

    def test_exclude_test(self):
        from ptah import config

        self.assertFalse(config.exclude('blah.test'))
        self.assertFalse(config.exclude('blah.ftest'))
        self.assertFalse(config.exclude('blah.subpkg', ('blah.',)))
        self.assertTrue(config.exclude('blah.subpkg'))

    def test_loadpackages(self):
        from ptah import config

        self.assertEqual(
            config.list_packages(('ptah',), excludes=('ptah',)), [])

        self.assertIn('ptah', config.list_packages())
        self.assertEqual(config.list_packages(excludes=('ptah',)), [])

    def test_stop_exc(self):
        from ptah import config

        err = ValueError('test')

        exc = config.StopException(err)
        self.assertIs(exc.exc, err)
        self.assertEqual(str(exc), '\ntest')