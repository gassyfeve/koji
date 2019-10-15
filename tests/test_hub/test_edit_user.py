import mock
import unittest

import koji
import kojihub

UP = kojihub.UpdateProcessor

class TestEditUser(unittest.TestCase):

    def getUpdate(self, *args, **kwargs):
        update = UP(*args, **kwargs)
        update.execute = mock.MagicMock()
        self.updates.append(update)
        return update

    def setUp(self):
        self.updates = []
        self._singleValue = mock.patch('kojihub._singleValue').start()
        self.get_user = mock.patch('kojihub.get_user').start()
        self.context = mock.patch('kojihub.context').start()
        self.UpdateProcessor = mock.patch('kojihub.UpdateProcessor',
                                          side_effect=self.getUpdate).start()
        # It seems MagicMock will not automatically handle attributes that
        # start with "assert"
        self.context.session.assertLogin = mock.MagicMock()

    def tearDown(self):
        mock.patch.stopall()

    def test_edit(self):
        self.get_user.return_value = {'id': 333,
                                     'name': 'user',
                                     'krb_principal': 'krb'}
        self._singleValue.return_value = None

        kojihub._edit_user('user', name='newuser', krb_principal='krb')
        # check the update
        self.assertEqual(len(self.updates), 1)
        update = self.updates[0]
        self.assertEqual(update.table, 'users')
        self.assertEqual(update.data, {'name': 'newuser'})
        self.assertEqual(update.values, {'userID': 333})
        self.assertEqual(update.clauses, ['id = %(userID)i'])

        kojihub._edit_user('user', name='user', krb_principal='newkrb')
        # check the insert/update
        self.assertEqual(len(self.updates), 2)
        update = self.updates[1]
        self.assertEqual(update.table, 'users')
        self.assertEqual(update.data, {'krb_principal': 'newkrb'})
        self.assertEqual(update.values, {'userID': 333})
        self.assertEqual(update.clauses, ['id = %(userID)i'])

        self._singleValue.reset_mock()
        self._singleValue.return_value = 2
        with self.assertRaises(koji.GenericError) as cm:
            kojihub._edit_user('user', name='newuser')
        self._singleValue.assert_called_once()
        self.assertEqual(cm.exception.args[0], 'Name newuser already taken by user 2')