#!/usr/bin/env python
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright ©2016 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing client operations.

Clients and Client are 2 classes defined in this file.

Clients: Class for representing all the clients associated with the commcell

Client: Class for a single client of the commcell


Clients:
    __init__(commcell_object) -- initialise object of Clients class associated with the commcell
    __str__()                 -- returns all the clients associated with the commcell
    __repr__()                -- returns the string to represent the instance of the Clients class
    _get_clients()            -- gets all the clients associated with the commcell
    has_client(client_name)   -- checks if a client exists with the given name or not
    get(client_name)          -- returns the Client class object of the input client name
    delete(client_name)       -- deletes the client specified by the client name from the commcell


Client:
    __init__(commcell_object,
             client_name,
             client_id=None)     --  initialise object of Class with the specified client name
                                         and id, and associated to the commcell
    __repr__()                   --  return the client name and id, the instance is associated with
    _get_client_id()             --  method to get the client id, if not specified in __init__
    _get_client_properties()     --  get the properties of this client
    enable_backup()              --  enables the backup for the client
    enable_backup_at_time()      --  enables the backup for the client at the input time specified
    disble_backup()              --  disbles the backup for the client
    enable_restore()             --  enables the restore for the client
    enable_restore_at_time()     --  enables the restore for the client at the input time specified
    disble_restore()             --  disbles the restore for the client
    enable_data_aging()          --  enables the data aging for the client
    enable_data_aging_at_time()  --  enables the data aging for the client at input time specified
    disable_data_aging()         --  disbles the data aging for the clientt

"""

from __future__ import absolute_import

import time

from .agent import Agents
from .schedules import Schedules
from .exception import SDKException


class Clients(object):
    """Class for getting all the clients associated with the commcell."""

    def __init__(self, commcell_object):
        """Initialize object of the Clients class.

            Args:
                commcell_object (object)  --  instance of the Commcell class

            Returns:
                object - instance of the Clients class
        """
        self._commcell_object = commcell_object
        self._CLIENTS = self._commcell_object._services.GET_ALL_CLIENTS
        self._clients = self._get_clients()

    def __str__(self):
        """Representation string consisting of all clients of the commcell.

            Returns:
                str - string of all the clients associated with the commcell
        """
        representation_string = '{:^5}\t{:^20}\n\n'.format('S. No.', 'Client')

        for index, client in enumerate(self._clients):
            sub_str = '{:^5}\t{:20}\n'.format(index + 1, client)
            representation_string += sub_str

        return representation_string.strip()

    def __repr__(self):
        """Representation string for the instance of the Clients class."""
        return "Clients class instance for Commcell: '{0}'".format(
            self._commcell_object._headers['Host']
        )

    def _get_clients(self):
        """Gets all the clients associated with the commcell

            Returns:
                dict - consists of all clients in the commcell
                    {
                         "client1_name": client1_id,
                         "client2_name": client2_id
                    }

            Raises:
                SDKException:
                    if response is empty
                    if response is not success
        """
        flag, response = self._commcell_object._cvpysdk_object.make_request('GET', self._CLIENTS)

        if flag:
            if response.json() and 'clientProperties' in response.json():
                clients_dict = {}

                for dictionary in response.json()['clientProperties']:
                    temp_name = str(dictionary['client']['clientEntity']['clientName']).lower()
                    temp_id = str(dictionary['client']['clientEntity']['clientId']).lower()
                    clients_dict[temp_name] = temp_id

                return clients_dict
            else:
                raise SDKException('Response', '102')
        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    def has_client(self, client_name):
        """Checks if a client exists in the commcell with the input client name.

            Args:
                client_name (str)  --  name of the client

            Returns:
                bool - boolean output whether the client exists in the commcell or not

            Raises:
                SDKException:
                    if type of the client name argument is not string
        """
        if not isinstance(client_name, str):
            raise SDKException('Client', '101')

        return self._clients and str(client_name).lower() in self._clients

    def get(self, client_name):
        """Returns a client object of the specified client name.

            Args:
                client_name (str)  --  name of the client

            Returns:
                object - instance of the Client class for the given client name

            Raises:
                SDKException:
                    if type of the client name argument is not string
                    if no client exists with the given name
        """
        if not isinstance(client_name, str):
            raise SDKException('Client', '101')
        else:
            client_name = str(client_name).lower()

            if self.has_client(client_name):
                return Client(self._commcell_object, client_name, self._clients[client_name])

            raise SDKException(
                'Client', '102', 'No client exists with name: {0}'.format(client_name)
            )

    def delete(self, client_name):
        """Deletes the client from the commcell.

            Args:
                client_name (str)  --  name of the client to remove from the commcell

            Returns:
                None

            Raises:
                SDKException:
                    if type of the client name argument is not string
                    if response is empty
                    if response is not success
                    if no client exists with the given name
        """
        if not isinstance(client_name, str):
            raise SDKException('Client', '101')
        else:
            client_name = str(client_name).lower()

            if self.has_client(client_name):
                client_id = self._clients[client_name]
                client_delete_service = self._commcell_object._services.CLIENT % (client_id)
                client_delete_service += "?forceDelete=1"

                flag, response = self._commcell_object._cvpysdk_object.make_request(
                    'DELETE', client_delete_service
                )

                error_code = warning_code = 0

                if flag:
                    if response.json():
                        if 'response' in response.json():
                            if response.json()['response'][0]['errorCode'] == 0:
                                # initialize the clients again
                                # so the client object has all the clients
                                self._clients = self._get_clients()
                        else:
                            if 'errorCode' in response.json():
                                error_code = response.json()['errorCode']

                            if 'warningCode' in response.json():
                                warning_code = response.json()['warningCode']

                            o_str = 'Failed to delete client'

                            if error_code != 0:
                                error_message = response.json()['errorMessage']
                                if error_message:
                                    o_str += '\nError: "{0}"'.format(error_message)
                            elif warning_code != 0:
                                warning_message = response.json()['warningMessage']
                                if warning_message:
                                    o_str += '\nWarning: "{0}"'.format(warning_message)

                            raise SDKException('Client', '102', o_str)
                    else:
                        raise SDKException('Response', '102')
                else:
                    response_string = self._commcell_object._update_response_(response.text)
                    exception_message = 'Failed to delete the client\nError: "{0}"'

                    raise SDKException('Client', '102', exception_message.format(response_string))
            else:
                raise SDKException(
                    'Client', '102', 'No client exists with name: {0}'.format(client_name)
                )


class Client(object):
    """Class for performing client operations for a specific client."""

    def __init__(self, commcell_object, client_name, client_id=None):
        """Initialise the Client class instance.

            Args:
                commcell_object (object)  --  instance of the Commcell class
                client_name     (str)     --  name of the client
                client_id       (str)     --  id of the client
                    default: None

            Returns:
                object - instance of the Client class
        """
        self._commcell_object = commcell_object
        self._client_name = str(client_name).lower()

        if client_id:
            self._client_id = str(client_id)
        else:
            self._client_id = self._get_client_id()

        self._CLIENT = self._commcell_object._services.CLIENT % (self.client_id)
        self.properties = self._get_client_properties()

        self.agents = Agents(self)
        self.schedules = Schedules(self)

    def __repr__(self):
        """String representation of the instance of this class."""
        representation_string = 'Client class instance for Client: "{0}"'
        return representation_string.format(self.client_name)

    def _get_client_id(self):
        """Gets the client id associated with this client.

            Returns:
                str - id associated with this client
        """
        clients = Clients(self._commcell_object)
        return clients.get(self.client_name).client_id

    def _get_client_properties(self):
        """Gets the client properties of this client.

            Returns:
                dict - dictionary consisting of the properties of this client

            Raises:
                SDKException:
                    if response is empty
                    if response is not success
        """
        flag, response = self._commcell_object._cvpysdk_object.make_request('GET', self._CLIENT)

        if flag:
            if response.json() and 'clientProperties' in response.json():
                client_properties = response.json()['clientProperties'][0]

                os_info = client_properties['client']['osInfo']
                processor_type = os_info['OsDisplayInfo']['ProcessorType']
                os_name = os_info['OsDisplayInfo']['OSName']

                self._os_info = '{0} {1} {2}  --  {3}'.format(
                    processor_type,
                    os_info['Type'],
                    os_info['SubType'],
                    os_name
                )

                client_props = client_properties['clientProps']

                if client_props['activityControl']['EnableDataRecovery'] is True:
                    self._data_recovery = 'Enabled'
                else:
                    self._data_recovery = 'Disabled'

                if client_props['activityControl']['EnableDataManagement'] is True:
                    self._data_management = 'Enabled'
                else:
                    self._data_management = 'Disabled'

                if client_props['activityControl']['EnableOnlineContentIndex'] is True:
                    self._online_content_index = 'Enabled'
                else:
                    self._online_content_index = 'Disabled'

                activities = client_props["clientActivityControl"]["activityControlOptions"]

                for activity in activities:
                    if activity["activityType"] == 1:
                        if activity["enableActivityType"] is True:
                            self._backup = 'Enabled'
                        else:
                            self._backup = 'Disabled'
                    elif activity["activityType"] == 2:
                        if activity["enableActivityType"] is True:
                            self._restore = 'Enabled'
                        else:
                            self._restore = 'Disabled'
                    elif activity["activityType"] == 16:
                        if activity["enableActivityType"] is True:
                            self._data_aging = 'Enabled'
                        else:
                            self._data_aging = 'Disabled'
            else:
                raise SDKException('Response', '102')
        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    def _request_json_(self, option, enable=True, enable_time=None):
        """Returns the JSON request to pass to the API as per the options selected by the user.

            Args:
                option (str)  --  string option for which to run the API for
                    e.g.; Backup / Restore / Data Aging

            Returns:
                dict - JSON request to pass to the API
        """
        options_dict = {
            "Backup": 1,
            "Restore": 2,
            "Data Aging": 16
        }

        request_json1 = {
            "association": {
                "entity": [{
                    "clientName": self.client_name
                }]
            },
            "clientProperties": {
                "clientProps": {
                    "clientActivityControl": {
                        "activityControlOptions": [{
                            "activityType": options_dict[option],
                            "enableAfterADelay": False,
                            "enableActivityType": enable
                        }]
                    }
                }
            }
        }

        request_json2 = {
            "association": {
                "entity": [{
                    "clientName": self.client_name
                }]
            },
            "clientProperties": {
                "clientProps": {
                    "clientActivityControl": {
                        "activityControlOptions": [{
                            "activityType": options_dict[option],
                            "enableAfterADelay": True,
                            "enableActivityType": False,
                            "dateTime": {
                                "TimeZoneName": "(UTC) Coordinated Universal Time",
                                "timeValue": enable_time
                            }
                        }]
                    }
                }
            }
        }

        if enable_time:
            return request_json2
        else:
            return request_json1

    @property
    def client_id(self):
        """Treats the client id as a read-only attribute."""
        return self._client_id

    @property
    def client_name(self):
        """Treats the client name as a read-only attribute."""
        return self._client_name

    @property
    def os_info(self):
        """Treats the os information as a read-only attribute."""
        return self._os_info

    @property
    def data_recovery(self):
        """Treats the data recovery as a read-only attribute."""
        return self._data_recovery

    @property
    def data_management(self):
        """Treats the data management as a read-only attribute."""
        return self._data_management

    @property
    def online_content_index(self):
        """Treats the online content index as a read-only attribute."""
        return self._online_content_index

    @property
    def backup(self):
        """Treats the backup as a read-only attribute."""
        return self._backup

    @property
    def restore(self):
        """Treats the restore as a read-only attribute."""
        return self._restore

    @property
    def data_aging(self):
        """Treats the data aging as a read-only attribute."""
        return self._data_aging

    def enable_backup(self):
        """Enable Backup for this Client.

            Raises:
                SDKException:
                    if failed to enable backup
                    if response is empty
                    if response is not success
        """
        request_json = self._request_json_('Backup')

        flag, response = self._commcell_object._cvpysdk_object.make_request(
            'POST', self._CLIENT, request_json
        )

        if flag:
            if response.json() and 'response' in response.json():
                error_code = response.json()['response'][0]['errorCode']

                if error_code == 0:
                    return
                elif 'errorMessage' in response.json()['response'][0]:
                    error_message = response.json()['response'][0]['errorMessage']

                    o_str = 'Failed to enable Backup\nError: "{0}"'.format(error_message)
                    raise SDKException('Client', '102', o_str)
            else:
                raise SDKException('Response', '102')
        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    def enable_backup_at_time(self, enable_time):
        """Disables Backup if not already disabled, and enables at the time specified.

            Args:
                enable_time (str)  --  UTC time to enable the backup at, in 24 Hour format
                    format: YYYY-MM-DD HH:mm:ss

            Raises:
                SDKException:
                    if time value entered is less than the current time
                    if time value entered is not of correct format
                    if failed to enable backup
                    if response is empty
                    if response is not success
        """
        try:
            time_tuple = time.strptime(enable_time, "%Y-%m-%d %H:%M:%S")
            if time.mktime(time_tuple) < time.time():
                raise SDKException('Client', '103')
        except ValueError:
            raise SDKException('Client', '104')

        request_json = self._request_json_('Backup', False, enable_time)

        flag, response = self._commcell_object._cvpysdk_object.make_request(
            'POST', self._CLIENT, request_json
        )

        if flag:
            if response.json() and 'response' in response.json():
                error_code = response.json()['response'][0]['errorCode']

                if error_code == 0:
                    return
                elif 'errorMessage' in response.json()['response'][0]:
                    error_message = response.json()['response'][0]['errorMessage']

                    o_str = 'Failed to enable Backup\nError: "{0}"'.format(error_message)
                    raise SDKException('Client', '102', o_str)
            else:
                raise SDKException('Response', '102')
        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    def disable_backup(self):
        """Disables Backup for this Client.

            Raises:
                SDKException:
                    if failed to disable backup
                    if response is empty
                    if response is not success
        """
        request_json = self._request_json_('Backup', False)

        flag, response = self._commcell_object._cvpysdk_object.make_request(
            'POST', self._CLIENT, request_json
        )

        if flag:
            if response.json() and 'response' in response.json():
                error_code = response.json()['response'][0]['errorCode']

                if error_code == 0:
                    return
                elif 'errorMessage' in response.json()['response'][0]:
                    error_message = response.json()['response'][0]['errorMessage']

                    o_str = 'Failed to disable Backup\nError: "{0}"'.format(error_message)
                    raise SDKException('Client', '102', o_str)
            else:
                raise SDKException('Response', '102')
        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    def enable_restore(self):
        """Enable Restore for this Client.

            Raises:
                SDKException:
                    if failed to enable restore
                    if response is empty
                    if response is not success
        """
        request_json = self._request_json_('Restore')

        flag, response = self._commcell_object._cvpysdk_object.make_request(
            'POST', self._CLIENT, request_json
        )

        if flag:
            if response.json() and 'response' in response.json():
                error_code = response.json()['response'][0]['errorCode']

                if error_code == 0:
                    return
                elif 'errorMessage' in response.json()['response'][0]:
                    error_message = response.json()['response'][0]['errorMessage']

                    o_str = 'Failed to enable Restore\nError: "{0}"'.format(error_message)
                    raise SDKException('Client', '102', o_str)
            else:
                raise SDKException('Response', '102')
        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    def enable_restore_at_time(self, enable_time):
        """Disables Restore if not already disabled, and enables at the time specified.

            Args:
                enable_time (str)  --  UTC time to enable the restore at, in 24 Hour format
                    format: YYYY-MM-DD HH:mm:ss

            Raises:
                SDKException:
                    if time value entered is less than the current time
                    if time value entered is not of correct format
                    if failed to enable restore
                    if response is empty
                    if response is not success
        """
        try:
            time_tuple = time.strptime(enable_time, "%Y-%m-%d %H:%M:%S")
            if time.mktime(time_tuple) < time.time():
                raise SDKException('Client', '103')
        except ValueError:
            raise SDKException('Client', '104')

        request_json = self._request_json_('Restore', False, enable_time)

        flag, response = self._commcell_object._cvpysdk_object.make_request(
            'POST', self._CLIENT, request_json
        )

        if flag:
            if response.json() and 'response' in response.json():
                error_code = response.json()['response'][0]['errorCode']

                if error_code == 0:
                    return
                elif 'errorMessage' in response.json()['response'][0]:
                    error_message = response.json()['response'][0]['errorMessage']

                    o_str = 'Failed to enable Restore\nError: "{0}"'.format(error_message)
                    raise SDKException('Client', '102', o_str)
            else:
                raise SDKException('Response', '102')
        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    def disable_restore(self):
        """Disables Restore for this Client.

            Raises:
                SDKException:
                    if failed to disable restore
                    if response is empty
                    if response is not success
        """
        request_json = self._request_json_('Restore', False)

        flag, response = self._commcell_object._cvpysdk_object.make_request(
            'POST', self._CLIENT, request_json
        )

        if flag:
            if response.json() and 'response' in response.json():
                error_code = response.json()['response'][0]['errorCode']

                if error_code == 0:
                    return
                elif 'errorMessage' in response.json()['response'][0]:
                    error_message = response.json()['response'][0]['errorMessage']

                    o_str = 'Failed to disable Restore\nError: "{0}"'.format(error_message)
                    raise SDKException('Client', '102', o_str)
            else:
                raise SDKException('Response', '102')
        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    def enable_data_aging(self):
        """Enable Data Aging for this Client.

            Raises:
                SDKException:
                    if failed to enable data aging
                    if response is empty
                    if response is not success
        """
        request_json = self._request_json_('Data Aging')

        flag, response = self._commcell_object._cvpysdk_object.make_request(
            'POST', self._CLIENT, request_json
        )

        if flag:
            if response.json() and 'response' in response.json():
                error_code = response.json()['response'][0]['errorCode']

                if error_code == 0:
                    return
                elif 'errorMessage' in response.json()['response'][0]:
                    error_message = response.json()['response'][0]['errorMessage']

                    o_str = 'Failed to enable Data Aging\nError: "{0}"'.format(error_message)
                    raise SDKException('Client', '102', o_str)
            else:
                raise SDKException('Response', '102')
        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    def enable_data_aging_at_time(self, enable_time):
        """Disables Data Aging if not already disabled, and enables at the time specified.

            Args:
                enable_time (str)  --  UTC time to enable the data aging at, in 24 Hour format
                    format: YYYY-MM-DD HH:mm:ss

            Raises:
                SDKException:
                    if time value entered is less than the current time
                    if time value entered is not of correct format
                    if failed to enable data aging
                    if response is empty
                    if response is not success
        """
        try:
            time_tuple = time.strptime(enable_time, "%Y-%m-%d %H:%M:%S")
            if time.mktime(time_tuple) < time.time():
                raise SDKException('Client', '103')
        except ValueError:
            raise SDKException('Client', '104')

        request_json = self._request_json_('Data Aging', False, enable_time)

        flag, response = self._commcell_object._cvpysdk_object.make_request(
            'POST', self._CLIENT, request_json
        )

        if flag:
            if response.json() and 'response' in response.json():
                error_code = response.json()['response'][0]['errorCode']

                if error_code == 0:
                    return
                elif 'errorMessage' in response.json()['response'][0]:
                    error_message = response.json()['response'][0]['errorMessage']

                    o_str = 'Failed to enable Data Aging\nError: "{0}"'.format(error_message)
                    raise SDKException('Client', '102', o_str)
            else:
                raise SDKException('Response', '102')
        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    def disable_data_aging(self):
        """Disables Data Aging for this Client.

            Raises:
                SDKException:
                    if failed to disable data aging
                    if response is empty
                    if response is not success
        """
        request_json = self._request_json_('Data Aging', False)

        flag, response = self._commcell_object._cvpysdk_object.make_request(
            'POST', self._CLIENT, request_json
        )

        if flag:
            if response.json() and 'response' in response.json():
                error_code = response.json()['response'][0]['errorCode']

                if error_code == 0:
                    return
                elif 'errorMessage' in response.json()['response'][0]:
                    error_message = response.json()['response'][0]['errorMessage']

                    o_str = 'Failed to disable Data Aging\nError: "{0}"'.format(error_message)
                    raise SDKException('Client', '102', o_str)
            else:
                raise SDKException('Response', '102')
        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)
