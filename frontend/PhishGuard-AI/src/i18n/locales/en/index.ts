import type { Messages } from '@/i18n'
import base from './base'
import landing from './landing'
import auth from './auth'
import user from './user'
import admin from './admin'
import soc from './soc'
import ux from './ux'
import geo from './geo'

const messages: Messages = { ...base, ...landing, ...auth, ...user, ...admin, ...soc, ...ux, ...geo }
export default messages
