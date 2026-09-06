<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="de_DE">
<context>
    <name>AddCredentialJob</name>
    <message>
        <location filename="../secrets_tab/worker.py" line="+376"/>
        <source>A credential named &apos;{0}&apos; already exists.</source>
        <translation>Es gibt bereits Zugangsdaten mit dem Namen „{0}“.</translation>
    </message>
    <message>
        <location line="+27"/>
        <source>All other fields have to be empty when a URI is used.</source>
        <translation>Alle anderen Felder müssen leer sein, wenn eine URI verwendet wird.</translation>
    </message>
</context>
<context>
    <name>BackupRestoreUi</name>
    <message>
        <location filename="../secrets_tab/backup_restore_ui.py" line="+33"/>
        <source>Backup</source>
        <translation>Sicherung</translation>
    </message>
    <message>
        <location line="+0"/>
        <source>Restore</source>
        <translation>Wiederherstellung</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>Action: {0}</source>
        <translation>Aktion: {0}</translation>
    </message>
    <message>
        <location line="+5"/>
        <source>Cleartext</source>
        <translation>Klartext</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>This option disables encryption of the generated backup and is discouraged. Only use it for interoperability with other password managers.</source>
        <translation>Diese Option deaktiviert die Verschlüsselung der erzeugten Sicherung und wird nicht empfohlen. Verwenden Sie sie nur zur Kompatibilität mit anderen Passwort-Managern.</translation>
    </message>
    <message>
        <location line="+8"/>
        <source>The passphrase is created automatically during an encrypted backup.</source>
        <translation>Die Passphrase wird bei einer verschlüsselten Sicherung automatisch erzeugt.</translation>
    </message>
    <message>
        <location line="+6"/>
        <source>Copy passphrase</source>
        <translation>Passphrase kopieren</translation>
    </message>
    <message>
        <location line="+2"/>
        <source>Begin</source>
        <translation>Starten</translation>
    </message>
    <message>
        <location line="+11"/>
        <source>Passphrase</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+11"/>
        <source>Not passwords</source>
        <translation>Keine Passwörter</translation>
    </message>
    <message>
        <location line="+2"/>
        <source>Already exists</source>
        <translation>Bereits vorhanden</translation>
    </message>
    <message>
        <location line="+3"/>
        <location line="+77"/>
        <source>Successful</source>
        <translation>Erfolgreich</translation>
    </message>
    <message>
        <location line="-75"/>
        <source>The operation on these credentials completed successfully</source>
        <translation>Der Vorgang für diese Zugangsdaten wurde erfolgreich abgeschlossen</translation>
    </message>
    <message>
        <location line="+6"/>
        <source>Credentials without a password (for example OTP only) are skipped during the backup, as they cannot be extracted from the device.</source>
        <translation>Zugangsdaten ohne Passwort (zum Beispiel nur OTP) werden bei der Sicherung übersprungen, da sie nicht vom Gerät ausgelesen werden können.</translation>
    </message>
    <message>
        <location line="+5"/>
        <source>Credentials that were not imported because a credential with the same label already exists on the device</source>
        <translation>Zugangsdaten, die nicht importiert wurden, weil auf dem Gerät bereits Zugangsdaten mit demselben Namen vorhanden sind</translation>
    </message>
    <message>
        <location line="+5"/>
        <location line="+61"/>
        <source>Skipped</source>
        <translation>Übersprungen</translation>
    </message>
    <message>
        <location line="-59"/>
        <source>Credentials are skipped if they are PIN protected but no PIN was supplied.</source>
        <translation>Zugangsdaten werden übersprungen, wenn sie PIN-geschützt sind, aber keine PIN angegeben wurde.</translation>
    </message>
    <message>
        <location line="+18"/>
        <source>Status</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+14"/>
        <source>{0} ({1})</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+5"/>
        <source>Passphrase copied</source>
        <translation>Passphrase kopiert</translation>
    </message>
    <message>
        <location line="+2"/>
        <source>Nothing to copy</source>
        <translation>Nichts zu kopieren</translation>
    </message>
</context>
<context>
    <name>DeleteCredentialJob</name>
    <message>
        <location filename="../fido2_tab/worker.py" line="+225"/>
        <source>No FIDO2 PIN is set on this device</source>
        <translation>Auf diesem Gerät ist keine FIDO2-PIN gesetzt</translation>
    </message>
    <message>
        <location line="+41"/>
        <source>The passkey could not be deleted.</source>
        <translation>Der Passkey konnte nicht gelöscht werden.</translation>
    </message>
    <message>
        <location line="+6"/>
        <source>Passkey deleted</source>
        <translation>Passkey gelöscht</translation>
    </message>
</context>
<context>
    <name>EditCredentialJob</name>
    <message>
        <location filename="../secrets_tab/worker.py" line="-182"/>
        <source>There is no credential named &apos;{0}&apos;.</source>
        <translation>Es gibt keine Zugangsdaten mit dem Namen „{0}“.</translation>
    </message>
    <message>
        <location line="+8"/>
        <source>A credential named &apos;{0}&apos; already exists.</source>
        <translation>Es gibt bereits Zugangsdaten mit dem Namen „{0}“.</translation>
    </message>
</context>
<context>
    <name>ErrorDialog</name>
    <message>
        <location filename="../error_dialog.py" line="+21"/>
        <source>Save Log File</source>
        <translation>Protokoll speichern</translation>
    </message>
    <message>
        <location filename="../ui/error_dialog.ui" line="+14"/>
        <source>Error</source>
        <translation>Fehler</translation>
    </message>
    <message>
        <location line="+6"/>
        <source>An unexpected error occured.</source>
        <translation>Ein unerwarteter Fehler ist aufgetreten.</translation>
    </message>
</context>
<context>
    <name>Fido2PinUi</name>
    <message>
        <location filename="../fido2_tab/ui.py" line="+22"/>
        <source>Enter FIDO2 PIN</source>
        <translation>FIDO2-PIN eingeben</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>Please enter the FIDO2 PIN (remaining retries: {0}):</source>
        <translation>Bitte geben Sie die FIDO2-PIN ein (verbleibende Versuche: {0}):</translation>
    </message>
</context>
<context>
    <name>Fido2Tab</name>
    <message>
        <location filename="../fido2_tab/__init__.py" line="+92"/>
        <source>Display Name:</source>
        <translation>Anzeigename:</translation>
    </message>
    <message>
        <location line="+2"/>
        <source>Username:</source>
        <translation>Benutzername:</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>Credential ID:</source>
        <translation>Credential-ID:</translation>
    </message>
    <message>
        <location line="+32"/>
        <source>Passkeys</source>
        <translation>Passkeys</translation>
    </message>
    <message>
        <location line="+114"/>
        <source>(unknown)</source>
        <translation>(unbekannt)</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>(not set)</source>
        <translation>(nicht gesetzt)</translation>
    </message>
    <message>
        <location line="+21"/>
        <source>Delete Passkey</source>
        <translation>Passkey löschen</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>Permanently delete the passkey &apos;{0}&apos; from this device?</source>
        <translation>Passkey „{0}“ endgültig von diesem Gerät löschen?</translation>
    </message>
</context>
<context>
    <name>GUI</name>
    <message>
        <location filename="../gui.py" line="+41"/>
        <source>Managing passkeys requires administrator privileges on Windows. Please restart the Nitrokey App as administrator to list or delete passkeys.</source>
        <translation>Das Verwalten von Passkeys erfordert unter Windows Administratorrechte. Bitte starten Sie die Nitrokey App als Administrator neu, um Passkeys anzuzeigen oder zu löschen.</translation>
    </message>
    <message>
        <location line="+8"/>
        <source>A firmware update is in progress. Please wait until it has finished before closing the application.</source>
        <translation>Ein Firmware-Update läuft. Bitte warten Sie, bis es abgeschlossen ist, bevor Sie die Anwendung schließen.</translation>
    </message>
</context>
<context>
    <name>InfoBox</name>
    <message>
        <location filename="../information_box.py" line="+93"/>
        <source>Press your Nitrokey to confirm...</source>
        <translation>Drücken Sie Ihren Nitrokey zur Bestätigung ...</translation>
    </message>
    <message>
        <location line="+28"/>
        <source>Passwords PIN is cached - click to clear</source>
        <translation>Passwörter-PIN ist zwischengespeichert – zum Löschen klicken</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>Passwords PIN locked</source>
        <translation>Passwörter-PIN gesperrt</translation>
    </message>
</context>
<context>
    <name>ListCredentialsJob</name>
    <message>
        <location filename="../fido2_tab/worker.py" line="-128"/>
        <source>No FIDO2 PIN is set on this device</source>
        <translation>Auf diesem Gerät ist keine FIDO2-PIN gesetzt</translation>
    </message>
    <message>
        <location line="+32"/>
        <source>The passkeys could not be read from the device.</source>
        <translation>Die Passkeys konnten nicht vom Gerät gelesen werden.</translation>
    </message>
</context>
<context>
    <name>MainWindow</name>
    <message>
        <location filename="../ui/mainwindow.ui" line="+29"/>
        <source>Nitrokey App</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+102"/>
        <source>Test Text</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+29"/>
        <source>TextLabel</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+97"/>
        <source>Please insert
 your Nitrokey</source>
        <translation>Bitte stecken Sie
Ihren Nitrokey ein</translation>
    </message>
    <message>
        <location line="+86"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;home&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Start&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location line="+53"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;help&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Hilfe&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
</context>
<context>
    <name>Nk3Button</name>
    <message>
        <location filename="../nk3_button.py" line="+106"/>
        <source>Touch your Nitrokey 3</source>
        <translation>Berühren Sie Ihren Nitrokey 3</translation>
    </message>
</context>
<context>
    <name>OverviewTab</name>
    <message>
        <location filename="../overview_tab/__init__.py" line="+60"/>
        <source>Overview</source>
        <translation>Übersicht</translation>
    </message>
    <message>
        <location line="+26"/>
        <source>Update your Nitrokey 3 for full functionality</source>
        <translation>Aktualisieren Sie Ihren Nitrokey 3 für den vollen Funktionsumfang</translation>
    </message>
    <message>
        <location line="+6"/>
        <source>Nitrokey 3 (old firmware)</source>
        <translation>Nitrokey 3 (alte Firmware)</translation>
    </message>
    <message>
        <location line="+9"/>
        <source>{0} Bootloader</source>
        <translation>{0}-Bootloader</translation>
    </message>
    <message>
        <location line="+43"/>
        <source>Please restart the application as an administrator to be able to update.</source>
        <translation>Bitte starten Sie die Anwendung als Administrator neu, um aktualisieren zu können.</translation>
    </message>
    <message>
        <location line="+6"/>
        <source>Please remove all Nitrokey devices except the one you want to update.</source>
        <translation>Bitte entfernen Sie alle Nitrokey-Geräte außer dem, das aktualisiert werden soll.</translation>
    </message>
    <message>
        <location line="+9"/>
        <source>Update is already running. Please wait.</source>
        <translation>Das Update läuft bereits. Bitte warten.</translation>
    </message>
    <message>
        <location line="+19"/>
        <source>{0} successfully updated</source>
        <translation>{0} erfolgreich aktualisiert</translation>
    </message>
    <message>
        <location line="+2"/>
        <location line="+5"/>
        <source>{0} update failed</source>
        <translation>{0}-Update fehlgeschlagen</translation>
    </message>
    <message>
        <location line="-3"/>
        <source>{0} update aborted</source>
        <translation>{0}-Update abgebrochen</translation>
    </message>
    <message>
        <location line="+7"/>
        <source>{0}: {1}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../ui/overview_tab.ui" line="+20"/>
        <source>Form</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+132"/>
        <source>Nitrokey 3</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+27"/>
        <source>UUID:</source>
        <translation>UUID:</translation>
    </message>
    <message>
        <location line="+15"/>
        <location line="+42"/>
        <location line="+42"/>
        <location line="+42"/>
        <location line="+44"/>
        <source>TextLabel</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="-143"/>
        <source>Path:</source>
        <translation>Pfad:</translation>
    </message>
    <message>
        <location line="+42"/>
        <source>Version:</source>
        <translation>Version:</translation>
    </message>
    <message>
        <location line="+42"/>
        <source>Variant:</source>
        <translation>Variante:</translation>
    </message>
    <message>
        <location line="+42"/>
        <source>Init status:</source>
        <translation>Init-Status:</translation>
    </message>
    <message>
        <location line="+44"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;An error occurred during device initialization. &lt;br/&gt;Click &lt;span style=&quot; font-weight:600; text-decoration: underline; color:#c0392b;&quot;&gt;More Info&lt;/span&gt; for more information and contact support if the error persists.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Bei der Initialisierung des Geräts ist ein Fehler aufgetreten. &lt;br/&gt;Klicken Sie auf &lt;span style=&quot; font-weight:600; text-decoration: underline; color:#c0392b;&quot;&gt;Mehr Infos&lt;/span&gt; für weitere Informationen und wenden Sie sich an den Support, falls der Fehler bestehen bleibt.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location line="+33"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href=&quot;https://docs.nitrokey.com/nitrokey3/&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#c0392b;&quot;&gt;More Info&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href=&quot;https://docs.nitrokey.com/nitrokey3/&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#c0392b;&quot;&gt;Mehr Infos&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location line="+48"/>
        <source>Check for Update</source>
        <translation>Nach Update suchen</translation>
    </message>
    <message>
        <location line="+14"/>
        <source>Update with local Firmware</source>
        <translation>Mit lokaler Firmware aktualisieren</translation>
    </message>
</context>
<context>
    <name>PinUi</name>
    <message numerus="yes">
        <location filename="../secrets_tab/ui.py" line="+26"/>
        <source>Enter Passwords PIN - %n attempt(s) remaining</source>
        <translation>
            <numerusform>Passwörter-PIN eingeben – noch %n Versuch</numerusform>
            <numerusform>Passwörter-PIN eingeben – noch %n Versuche</numerusform>
        </translation>
    </message>
    <message numerus="yes">
        <location line="+2"/>
        <source>Enter the Passwords PIN.

WARNING: only %n attempt(s) remaining before the device locks permanently.</source>
        <translation>
            <numerusform>Geben Sie die Passwörter-PIN ein.

WARNUNG: Nur noch %n Versuch, bevor das Gerät dauerhaft gesperrt wird.</numerusform>
            <numerusform>Geben Sie die Passwörter-PIN ein.

WARNUNG: Nur noch %n Versuche, bevor das Gerät dauerhaft gesperrt wird.</numerusform>
        </translation>
    </message>
    <message>
        <location line="+6"/>
        <source>Enter Passwords PIN</source>
        <translation>Passwörter-PIN eingeben</translation>
    </message>
    <message numerus="yes">
        <location line="+1"/>
        <source>Enter the Passwords PIN (%n attempt(s) remaining):</source>
        <translation>
            <numerusform>Geben Sie die Passwörter-PIN ein (noch %n Versuch):</numerusform>
            <numerusform>Geben Sie die Passwörter-PIN ein (noch %n Versuche):</numerusform>
        </translation>
    </message>
    <message>
        <location line="+15"/>
        <source>Set Passwords PIN</source>
        <translation>Passwörter-PIN festlegen</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>Please enter the new PIN for Passwords:</source>
        <translation>Bitte geben Sie die neue PIN für Passwörter ein:</translation>
    </message>
    <message>
        <location line="+10"/>
        <source>Confirm Passwords PIN</source>
        <translation>Passwörter-PIN bestätigen</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>Please confirm the new PIN for Passwords:</source>
        <translation>Bitte bestätigen Sie die neue PIN für Passwörter:</translation>
    </message>
    <message>
        <location line="+12"/>
        <source>PIN Mismatch</source>
        <translation>PINs stimmen nicht überein</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>The PINs you entered do not match. The PIN has not been changed.</source>
        <translation>Die eingegebenen PINs stimmen nicht überein. Die PIN wurde nicht geändert.</translation>
    </message>
</context>
<context>
    <name>ResetFido</name>
    <message>
        <location filename="../settings_tab/worker.py" line="+167"/>
        <source>FIDO2 was reset successfully</source>
        <translation>FIDO2 wurde erfolgreich zurückgesetzt</translation>
    </message>
    <message>
        <location line="+5"/>
        <source>The device has been connected for more than 10 seconds. Please re-plug it to reset FIDO2.</source>
        <translation>Das Gerät ist seit mehr als 10 Sekunden angeschlossen. Bitte stecken Sie es neu ein, um FIDO2 zurückzusetzen.</translation>
    </message>
</context>
<context>
    <name>ResetPasswords</name>
    <message>
        <location line="+30"/>
        <source>Passwords was reset successfully</source>
        <translation>Passwörter wurde erfolgreich zurückgesetzt</translation>
    </message>
</context>
<context>
    <name>SaveFidoPinJob</name>
    <message>
        <location line="-106"/>
        <source>FIDO2 PIN changed</source>
        <translation>FIDO2-PIN geändert</translation>
    </message>
</context>
<context>
    <name>SavePasswordsPinJob</name>
    <message>
        <location line="+44"/>
        <source>Passwords PIN changed</source>
        <translation>Passwörter-PIN geändert</translation>
    </message>
</context>
<context>
    <name>SecretsTab</name>
    <message>
        <location filename="../secrets_tab/__init__.py" line="+217"/>
        <source>Generate random password</source>
        <translation>Zufälliges Passwort erzeugen</translation>
    </message>
    <message>
        <location line="+99"/>
        <source>Passwords</source>
        <translation>Passwörter</translation>
    </message>
    <message>
        <location line="+101"/>
        <source>Secret is generated</source>
        <translation>Secret wurde erzeugt</translation>
    </message>
    <message>
        <location line="+18"/>
        <source>Backup passwords</source>
        <translation>Passwörter sichern</translation>
    </message>
    <message>
        <location line="+6"/>
        <source>Save Credential Backup</source>
        <translation>Sicherung der Zugangsdaten speichern</translation>
    </message>
    <message>
        <location line="+2"/>
        <location line="+11"/>
        <source>JSON Files (*.json)</source>
        <translation>JSON-Dateien (*.json)</translation>
    </message>
    <message>
        <location line="+0"/>
        <source>Open Credential Backup</source>
        <translation>Sicherung der Zugangsdaten öffnen</translation>
    </message>
    <message>
        <location line="+7"/>
        <source>Restore passwords from {0}</source>
        <translation>Passwörter aus {0} wiederherstellen</translation>
    </message>
    <message>
        <location line="+124"/>
        <location line="+493"/>
        <source>&lt;hidden&gt;</source>
        <translation>&lt;verborgen&gt;</translation>
    </message>
    <message>
        <location line="-397"/>
        <source>&lt;hidden - click to edit&gt;</source>
        <translation>&lt;verborgen – zum Bearbeiten klicken&gt;</translation>
    </message>
    <message>
        <location line="+6"/>
        <source>&lt;cannot edit&gt;</source>
        <translation>&lt;nicht bearbeitbar&gt;</translation>
    </message>
    <message>
        <location line="+6"/>
        <location line="+17"/>
        <location line="+41"/>
        <location line="+92"/>
        <location filename="../ui/secrets_tab.ui" line="+436"/>
        <location line="+44"/>
        <location line="+42"/>
        <location line="+39"/>
        <location line="+135"/>
        <source>&lt;empty&gt;</source>
        <translation>&lt;leer&gt;</translation>
    </message>
    <message>
        <location line="-48"/>
        <source>Credential cannot be saved:</source>
        <translation>Zugangsdaten können nicht gespeichert werden:</translation>
    </message>
    <message>
        <location line="+17"/>
        <location line="+1"/>
        <source>Enter a Credential Name</source>
        <translation>Geben Sie einen Namen ein</translation>
    </message>
    <message>
        <location line="+2"/>
        <location line="+1"/>
        <source>Credential Name is too short</source>
        <translation>Der Name ist zu kurz</translation>
    </message>
    <message>
        <location line="+3"/>
        <location line="+1"/>
        <source>Credential Name is too long</source>
        <translation>Der Name ist zu lang</translation>
    </message>
    <message>
        <location line="+4"/>
        <location line="+1"/>
        <source>Username is too long</source>
        <translation>Der Benutzername ist zu lang</translation>
    </message>
    <message>
        <location line="+4"/>
        <location line="+1"/>
        <source>Password is too long</source>
        <translation>Das Passwort ist zu lang</translation>
    </message>
    <message>
        <location line="+4"/>
        <location line="+1"/>
        <source>Comment is too long</source>
        <translation>Der Kommentar ist zu lang</translation>
    </message>
    <message>
        <location line="+5"/>
        <source>OTP not configured</source>
        <translation>OTP nicht eingerichtet</translation>
    </message>
    <message>
        <location line="+10"/>
        <location line="+3"/>
        <source>The HMAC-Secret is not 32 chars long</source>
        <translation>Das HMAC-Secret ist nicht 32 Zeichen lang</translation>
    </message>
    <message>
        <location line="+7"/>
        <location line="+1"/>
        <location line="+8"/>
        <location line="+1"/>
        <source>Invalid character in Secret</source>
        <translation>Ungültiges Zeichen im Secret</translation>
    </message>
    <message>
        <location line="-6"/>
        <location line="+1"/>
        <source>Secret is not in Base32</source>
        <translation>Das Secret ist nicht Base32-kodiert</translation>
    </message>
    <message>
        <location line="+8"/>
        <location line="+1"/>
        <source>Secret is not valid Base32</source>
        <translation>Das Secret ist kein gültiges Base32</translation>
    </message>
    <message>
        <location line="+4"/>
        <location line="+1"/>
        <source>Enter a Secret</source>
        <translation>Geben Sie ein Secret ein</translation>
    </message>
    <message>
        <location line="+4"/>
        <source>Save credential</source>
        <translation>Zugangsdaten speichern</translation>
    </message>
    <message>
        <location line="+7"/>
        <source>Contents copied to clipboard</source>
        <translation>In die Zwischenablage kopiert</translation>
    </message>
    <message>
        <location line="+67"/>
        <source>Select at least one character group to generate a password</source>
        <translation>Wählen Sie mindestens eine Zeichengruppe aus, um ein Passwort zu erzeugen</translation>
    </message>
    <message>
        <location line="+22"/>
        <source>Letters</source>
        <translation>Buchstaben</translation>
    </message>
    <message>
        <location line="+2"/>
        <source>Digits</source>
        <translation>Ziffern</translation>
    </message>
    <message>
        <location line="+2"/>
        <source>Symbols</source>
        <translation>Sonderzeichen</translation>
    </message>
    <message>
        <location line="+18"/>
        <source>Length:</source>
        <translation>Länge:</translation>
    </message>
    <message>
        <location line="+122"/>
        <source>Delete Credential</source>
        <translation>Zugangsdaten löschen</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>Delete &apos;{0}&apos; from the device?</source>
        <translation>„{0}“ vom Gerät löschen?</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>This action cannot be undone.</source>
        <translation>Diese Aktion kann nicht rückgängig gemacht werden.</translation>
    </message>
    <message>
        <location line="+1"/>
        <location filename="../ui/secrets_tab.ui" line="+206"/>
        <source>Delete</source>
        <translation>Löschen</translation>
    </message>
    <message>
        <location line="+73"/>
        <source>Idle</source>
        <translation>Bereit</translation>
    </message>
    <message>
        <location line="+5"/>
        <source>Backup complete</source>
        <translation>Sicherung abgeschlossen</translation>
    </message>
    <message>
        <location line="+2"/>
        <source>Restore complete</source>
        <translation>Wiederherstellung abgeschlossen</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>Working... Press your Nitrokey if it blinks.</source>
        <translation>Vorgang läuft ... Drücken Sie Ihren Nitrokey, wenn er blinkt.</translation>
    </message>
    <message>
        <location line="+12"/>
        <source>The backup is encrypted. Please enter the passphrase.</source>
        <translation>Die Sicherung ist verschlüsselt. Bitte geben Sie die Passphrase ein.</translation>
    </message>
    <message>
        <location line="+5"/>
        <source>The backup is not encrypted, the passphrase is ignored.</source>
        <translation>Die Sicherung ist nicht verschlüsselt, die Passphrase wird ignoriert.</translation>
    </message>
    <message>
        <location line="+10"/>
        <source>The backup file could not be read.</source>
        <translation>Die Sicherungsdatei konnte nicht gelesen werden.</translation>
    </message>
    <message>
        <location filename="../ui/secrets_tab.ui" line="-882"/>
        <source>Form</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+93"/>
        <source>Refresh</source>
        <translation>Aktualisieren</translation>
    </message>
    <message>
        <location line="+32"/>
        <source>Add</source>
        <translation>Hinzufügen</translation>
    </message>
    <message>
        <location line="+55"/>
        <source>Export</source>
        <translation>Exportieren</translation>
    </message>
    <message>
        <location line="+38"/>
        <source>Import</source>
        <translation>Importieren</translation>
    </message>
    <message>
        <location line="+19"/>
        <source>Show Protected Passwords</source>
        <translation>Geschützte Passwörter anzeigen</translation>
    </message>
    <message>
        <location line="+116"/>
        <source>dummy</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+24"/>
        <source>&lt;insert credential name&gt;</source>
        <translation>&lt;Namen eingeben&gt;</translation>
    </message>
    <message>
        <location line="+12"/>
        <source>URI:</source>
        <translation>URI:</translation>
    </message>
    <message>
        <location line="+44"/>
        <source>Username:</source>
        <translation>Benutzername:</translation>
    </message>
    <message>
        <location line="+42"/>
        <source>Password:</source>
        <translation>Passwort:</translation>
    </message>
    <message>
        <location line="+45"/>
        <source>Comment:</source>
        <translation>Kommentar:</translation>
    </message>
    <message>
        <location line="+73"/>
        <location line="+13"/>
        <source>Password only</source>
        <translation>Nur Passwort</translation>
    </message>
    <message>
        <location line="+42"/>
        <source>algorithm</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+52"/>
        <source>%v s</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+15"/>
        <source>Require PIN:</source>
        <translation>PIN erforderlich:</translation>
    </message>
    <message>
        <location line="+45"/>
        <source>Require Touch:</source>
        <translation>Berührung erforderlich:</translation>
    </message>
    <message>
        <location line="+100"/>
        <source>Cancel</source>
        <translation>Abbrechen</translation>
    </message>
    <message>
        <location line="+44"/>
        <source>Save</source>
        <translation>Speichern</translation>
    </message>
    <message>
        <location line="+25"/>
        <source>Edit</source>
        <translation>Bearbeiten</translation>
    </message>
    <message>
        <location line="+48"/>
        <source>Please update the firmware on the device to use this feature.</source>
        <translation>Bitte aktualisieren Sie die Firmware des Geräts, um diese Funktion zu nutzen.</translation>
    </message>
</context>
<context>
    <name>SettingsTab</name>
    <message>
        <location filename="../settings_tab/__init__.py" line="+46"/>
        <source>FIDO2 is an authentication standard that enables secure and passwordless access to online services. It uses public key cryptography to provide strong authentication and protect against phishing and other security threats.</source>
        <translation>FIDO2 ist ein Authentifizierungsstandard für den sicheren und passwortlosen Zugang zu Online-Diensten. Er nutzt Public-Key-Kryptografie für eine starke Authentifizierung und schützt vor Phishing und anderen Sicherheitsbedrohungen.</translation>
    </message>
    <message>
        <location line="+11"/>
        <location line="+30"/>
        <source>PIN Change</source>
        <translation>PIN ändern</translation>
    </message>
    <message>
        <location line="-25"/>
        <location line="+30"/>
        <source>Factory Reset</source>
        <translation>Werksreset</translation>
    </message>
    <message>
        <location line="-29"/>
        <source>During a FIDO reset, the password is not set. All previously set credentials are removed. Any existing authentication data, such as U2F, Passkeys and FIDO2 authentication factors are deleted. After the reset, the user will need to re-register or re-enroll their authentication credentials to access the system or service again.</source>
        <translation>Bei einem FIDO-Reset wird kein Passwort gesetzt. Alle zuvor angelegten Zugangsdaten werden entfernt. Vorhandene Authentifizierungsdaten wie U2F, Passkeys und FIDO2-Faktoren werden gelöscht. Nach dem Zurücksetzen müssen die Zugangsdaten neu registriert werden, um wieder auf das System oder den Dienst zugreifen zu können.</translation>
    </message>
    <message>
        <location line="+13"/>
        <source>Passwords</source>
        <translation>Passwörter</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>Within Passwords various credentials and 2FAs like OTPs can be stored and managed. Supported are: Plain usernames using a password, HOTPs, TOTPs, ReverseHOTPs and HMAC.</source>
        <translation>In Passwörter lassen sich verschiedene Zugangsdaten und 2FA-Verfahren wie OTPs speichern und verwalten. Unterstützt werden: einfache Benutzernamen mit Passwort, HOTPs, TOTPs, ReverseHOTPs und HMAC.</translation>
    </message>
    <message>
        <location line="+16"/>
        <source>This operation will inevitably remove all your credentials in Passwords!</source>
        <translation>Dieser Vorgang entfernt unwiderruflich alle Ihre Zugangsdaten in Passwörter!</translation>
    </message>
    <message>
        <location line="+105"/>
        <location filename="../ui/settings_tab.ui" line="+99"/>
        <source>Settings</source>
        <translation>Einstellungen</translation>
    </message>
    <message>
        <location line="+162"/>
        <source>Cannot save</source>
        <translation>Speichern nicht möglich</translation>
    </message>
    <message>
        <location line="+26"/>
        <source>**Reset for FIDO2 is only possible within 10 seconds after plugging in the device.**</source>
        <translation>**Ein Reset von FIDO2 ist nur innerhalb von 10 Sekunden nach dem Einstecken des Geräts möglich.**</translation>
    </message>
    <message>
        <location line="+38"/>
        <source>Done - please use the new PIN to verify the key</source>
        <translation>Fertig – bitte bestätigen Sie den Schlüssel mit der neuen PIN</translation>
    </message>
    <message>
        <location line="+67"/>
        <source>&lt;insert old PIN&gt;</source>
        <translation>&lt;alte PIN eingeben&gt;</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>&lt;no PIN set&gt;</source>
        <translation>&lt;keine PIN gesetzt&gt;</translation>
    </message>
    <message>
        <location line="+13"/>
        <location line="+18"/>
        <source>PIN set</source>
        <translation>PIN gesetzt</translation>
    </message>
    <message>
        <location line="-18"/>
        <location line="+18"/>
        <source>yes</source>
        <translation>ja</translation>
    </message>
    <message>
        <location line="-18"/>
        <location line="+18"/>
        <source>no</source>
        <translation>nein</translation>
    </message>
    <message>
        <location line="-17"/>
        <location line="+18"/>
        <source>PIN retries</source>
        <translation>Verbleibende PIN-Versuche</translation>
    </message>
    <message>
        <location line="-18"/>
        <source>n/a</source>
        <translation>n. v.</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>Versions</source>
        <translation>Versionen</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>Extensions</source>
        <translation>Erweiterungen</translation>
    </message>
    <message>
        <location line="+17"/>
        <source>Version</source>
        <translation>Version</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>Serial</source>
        <translation>Seriennummer</translation>
    </message>
    <message>
        <location line="+32"/>
        <source>Credential cannot be saved:</source>
        <translation>Zugangsdaten können nicht gespeichert werden:</translation>
    </message>
    <message>
        <location line="+21"/>
        <source>Enter your Current Password</source>
        <translation>Geben Sie Ihr aktuelles Passwort ein</translation>
    </message>
    <message>
        <location line="+4"/>
        <source>Current Password is too short</source>
        <translation>Das aktuelle Passwort ist zu kurz</translation>
    </message>
    <message>
        <location line="+7"/>
        <location line="+2"/>
        <source>Enter your New Password</source>
        <translation>Geben Sie Ihr neues Passwort ein</translation>
    </message>
    <message>
        <location line="+5"/>
        <source>New Password is too short</source>
        <translation>Das neue Passwort ist zu kurz</translation>
    </message>
    <message>
        <location line="+6"/>
        <source>Repeat your New Password</source>
        <translation>Wiederholen Sie Ihr neues Passwort</translation>
    </message>
    <message>
        <location line="+5"/>
        <source>The repeated password is not equal</source>
        <translation>Die Wiederholung stimmt nicht überein</translation>
    </message>
    <message>
        <location line="+11"/>
        <source>Save credential</source>
        <translation>Zugangsdaten speichern</translation>
    </message>
    <message>
        <location filename="../ui/settings_tab.ui" line="-79"/>
        <source>Form</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+133"/>
        <source>Cancel</source>
        <translation>Abbrechen</translation>
    </message>
    <message>
        <location line="+22"/>
        <source>Reset</source>
        <translation>Zurücksetzen</translation>
    </message>
    <message>
        <location line="+22"/>
        <source>Save</source>
        <translation>Speichern</translation>
    </message>
    <message>
        <location line="+116"/>
        <source>dummy</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+28"/>
        <source>&lt;label 0&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+18"/>
        <source>&lt;value 0&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+13"/>
        <source>&lt;label 1&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+18"/>
        <source>&lt;value 1&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+13"/>
        <source>&lt;label 2&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+18"/>
        <source>&lt;value 2&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+13"/>
        <source>&lt;label 3&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+18"/>
        <source>&lt;value 3&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+13"/>
        <source>&lt;label 4&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+18"/>
        <source>&lt;value 4&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+13"/>
        <source>&lt;label 5&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+18"/>
        <source>&lt;value 5&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+22"/>
        <source>Current PIN:</source>
        <translation>Aktuelle PIN:</translation>
    </message>
    <message>
        <location line="+27"/>
        <location line="+62"/>
        <location line="+24"/>
        <source>&lt;empty&gt;</source>
        <translation>&lt;leer&gt;</translation>
    </message>
    <message>
        <location line="-70"/>
        <source>New PIN:</source>
        <translation>Neue PIN:</translation>
    </message>
    <message>
        <location line="+19"/>
        <source>Confirm New PIN:</source>
        <translation>Neue PIN bestätigen:</translation>
    </message>
    <message>
        <location line="+72"/>
        <source>[warning message box]</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+37"/>
        <source>[info message box]</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+27"/>
        <source>Please update the firmware on the device to use this feature.</source>
        <translation>Bitte aktualisieren Sie die Firmware des Geräts, um diese Funktion zu nutzen.</translation>
    </message>
</context>
<context>
    <name>VerifyPinJob</name>
    <message>
        <location filename="../secrets_tab/worker.py" line="-57"/>
        <source>The Passwords PIN could not be set.</source>
        <translation>Die Passwörter-PIN konnte nicht gesetzt werden.</translation>
    </message>
</context>
<context>
    <name>WelcomeTab</name>
    <message>
        <location filename="../welcome_tab.py" line="+70"/>
        <source>The language is set to {0} by {1}.</source>
        <translation>Die Sprache wird durch {1} auf {0} festgelegt.</translation>
    </message>
    <message>
        <location line="+24"/>
        <source>No connection</source>
        <translation>Keine Verbindung</translation>
    </message>
    <message>
        <location line="+7"/>
        <source>Update available</source>
        <translation>Update verfügbar</translation>
    </message>
    <message>
        <location line="+5"/>
        <source>App is up to date</source>
        <translation>App ist aktuell</translation>
    </message>
    <message>
        <location filename="../ui/welcome_tab.ui" line="+20"/>
        <source>Form</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+68"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;span style=&quot; font-size:14pt; font-weight:700;&quot;&gt;Welcome to the Nitrokey App&lt;/span&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;span style=&quot; font-size:14pt; font-weight:700;&quot;&gt;Willkommen in der Nitrokey App&lt;/span&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location line="+148"/>
        <source>This application allows you to administrate your Nitrokey 3</source>
        <translation>Mit dieser Anwendung verwalten Sie Ihren Nitrokey 3</translation>
    </message>
    <message>
        <location line="+13"/>
        <source>Your connected devices are visible on the left side</source>
        <translation>Ihre angeschlossenen Geräte sehen Sie links</translation>
    </message>
    <message>
        <location line="+13"/>
        <source>Select the device you want to manage</source>
        <translation>Wählen Sie das Gerät aus, das Sie verwalten möchten</translation>
    </message>
    <message>
        <location line="+61"/>
        <source>App version:</source>
        <translation>App-Version:</translation>
    </message>
    <message>
        <location line="+13"/>
        <source>1.0</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location line="+22"/>
        <source>Check for App Update</source>
        <translation>Nach App-Update suchen</translation>
    </message>
    <message>
        <location line="+43"/>
        <source>Language:</source>
        <translation>Sprache:</translation>
    </message>
    <message>
        <location line="+13"/>
        <source>Restart to apply</source>
        <translation>Neustart nötig</translation>
    </message>
    <message>
        <location line="+69"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href=&quot;https://docs.nitrokey.com/software/nk-app2/&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#c0392b;&quot;&gt;Instructions and help&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href=&quot;https://docs.nitrokey.com/software/nk-app2/&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#c0392b;&quot;&gt;Anleitung und Hilfe&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location line="+38"/>
        <source>Save Log File</source>
        <translation>Protokoll speichern</translation>
    </message>
</context>
<context>
    <name>errors</name>
    <message>
        <location filename="../error_messages.py" line="+21"/>
        <source>This device does not support Passwords.</source>
        <translation>Dieses Gerät unterstützt Passwörter nicht.</translation>
    </message>
    <message>
        <location line="+17"/>
        <source>The operation failed.</source>
        <translation>Der Vorgang ist fehlgeschlagen.</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>The operation failed: {0}</source>
        <translation>Der Vorgang ist fehlgeschlagen: {0}</translation>
    </message>
    <message>
        <location line="+6"/>
        <source>There is not enough space on the internal filesystem of the device to perform the firmware update. The release notes explain how to free some up: {0}</source>
        <translation>Auf dem internen Dateisystem des Geräts ist nicht genug Platz für das Firmware-Update. Die Release Notes erklären, wie Sie Platz schaffen: {0}</translation>
    </message>
    <message>
        <location line="+5"/>
        <source>The state of the device cannot be determined because its firmware is too old. Please update to firmware version v1.3.1 first.</source>
        <translation>Der Zustand des Geräts lässt sich nicht ermitteln, weil seine Firmware zu alt ist. Bitte aktualisieren Sie zuerst auf Firmware-Version v1.3.1.</translation>
    </message>
    <message>
        <location line="+5"/>
        <source>The Nitrokey SDK this application was built with is too old for the device. Please update the Nitrokey App and try again.</source>
        <translation>Das Nitrokey-SDK, mit dem diese Anwendung gebaut wurde, ist zu alt für das Gerät. Bitte aktualisieren Sie die Nitrokey App und versuchen Sie es erneut.</translation>
    </message>
    <message>
        <location line="+5"/>
        <source>The state of the device cannot be checked because it is already in bootloader mode. Please review the release notes before continuing: {0}</source>
        <translation>Der Zustand des Geräts lässt sich nicht prüfen, weil es bereits im Bootloader-Modus ist. Bitte lesen Sie die Release Notes, bevor Sie fortfahren: {0}</translation>
    </message>
    <message>
        <location line="+21"/>
        <source>The PIN is not correct.</source>
        <translation>Die PIN ist nicht korrekt.</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>The PIN is blocked because it was entered incorrectly too often. A factory reset of Passwords is needed to use it again.</source>
        <translation>Die PIN ist gesperrt, weil sie zu oft falsch eingegeben wurde. Um sie wieder zu nutzen, ist ein Werksreset von Passwörter nötig.</translation>
    </message>
    <message>
        <location line="+5"/>
        <source>The PIN has to be entered before this operation.</source>
        <translation>Für diesen Vorgang muss zuerst die PIN eingegeben werden.</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>The operation was not confirmed on the device.</source>
        <translation>Der Vorgang wurde am Gerät nicht bestätigt.</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>The credential was not found on the device.</source>
        <translation>Die Zugangsdaten wurden auf dem Gerät nicht gefunden.</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>There is not enough space left on the device for another credential.</source>
        <translation>Auf dem Gerät ist kein Platz für weitere Zugangsdaten.</translation>
    </message>
    <message>
        <location line="+3"/>
        <location line="+3"/>
        <source>The device rejected the data sent.</source>
        <translation>Das Gerät hat die gesendeten Daten abgelehnt.</translation>
    </message>
    <message>
        <location line="+3"/>
        <location line="+3"/>
        <location line="+3"/>
        <location line="+67"/>
        <location line="+3"/>
        <location line="+3"/>
        <source>This device does not support the requested operation.</source>
        <translation>Dieses Gerät unterstützt den angeforderten Vorgang nicht.</translation>
    </message>
    <message>
        <location line="-59"/>
        <source>The FIDO2 PIN is not correct.</source>
        <translation>Die FIDO2-PIN ist nicht korrekt.</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>The FIDO2 PIN is blocked because it was entered incorrectly too often. A factory reset of FIDO2 is needed to use it again.</source>
        <translation>Die FIDO2-PIN ist gesperrt, weil sie zu oft falsch eingegeben wurde. Um sie wieder zu nutzen, ist ein Werksreset von FIDO2 nötig.</translation>
    </message>
    <message>
        <location line="+5"/>
        <source>The FIDO2 PIN was entered incorrectly too often. Please remove the Nitrokey, insert it again and retry.</source>
        <translation>Die FIDO2-PIN wurde zu oft falsch eingegeben. Bitte ziehen Sie den Nitrokey ab, stecken Sie ihn wieder ein und versuchen Sie es erneut.</translation>
    </message>
    <message>
        <location line="+5"/>
        <source>The FIDO2 PIN authentication failed.</source>
        <translation>Die Authentifizierung mit der FIDO2-PIN ist fehlgeschlagen.</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>No FIDO2 PIN is set on this device.</source>
        <translation>Auf diesem Gerät ist keine FIDO2-PIN gesetzt.</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>The new FIDO2 PIN does not meet the requirements of the device.</source>
        <translation>Die neue FIDO2-PIN erfüllt die Anforderungen des Geräts nicht.</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>The FIDO2 PIN has to be entered again.</source>
        <translation>Die FIDO2-PIN muss erneut eingegeben werden.</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>The FIDO2 PIN has to be entered before this operation.</source>
        <translation>Für diesen Vorgang muss zuerst die FIDO2-PIN eingegeben werden.</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>There are no passkeys stored on this device.</source>
        <translation>Auf diesem Gerät sind keine Passkeys gespeichert.</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>There is no space left on the device for another passkey.</source>
        <translation>Auf dem Gerät ist kein Platz für einen weiteren Passkey.</translation>
    </message>
    <message>
        <location line="+3"/>
        <location line="+3"/>
        <source>The Nitrokey was not touched in time. Please try again.</source>
        <translation>Der Nitrokey wurde nicht rechtzeitig berührt. Bitte versuchen Sie es erneut.</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>The operation has to be confirmed by touching the Nitrokey.</source>
        <translation>Der Vorgang muss durch Berühren des Nitrokey bestätigt werden.</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>The device refused the operation.</source>
        <translation>Das Gerät hat den Vorgang verweigert.</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>The operation was cancelled.</source>
        <translation>Der Vorgang wurde abgebrochen.</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>The device does not allow this operation.</source>
        <translation>Das Gerät lässt diesen Vorgang nicht zu.</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>The fingerprint check is blocked. Please use the FIDO2 PIN instead.</source>
        <translation>Die Fingerabdruckprüfung ist gesperrt. Bitte verwenden Sie stattdessen die FIDO2-PIN.</translation>
    </message>
</context>
<context>
    <name>fido2</name>
    <message>
        <location filename="../fido2_tab/data.py" line="+26"/>
        <source>User verification optional</source>
        <translation>Nutzerverifizierung optional</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>User verification optional (with credential list)</source>
        <translation>Nutzerverifizierung optional (mit Credential-Liste)</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>User verification required</source>
        <translation>Nutzerverifizierung erforderlich</translation>
    </message>
    <message>
        <location line="+24"/>
        <source>(no name)</source>
        <translation>(kein Name)</translation>
    </message>
    <message>
        <location line="+46"/>
        <source>{0} stored</source>
        <translation>{0} gespeichert</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>up to {0} free</source>
        <translation>bis zu {0} frei</translation>
    </message>
    <message>
        <location line="+2"/>
        <source>Passkeys: {0}</source>
        <translation>Passkeys: {0}</translation>
    </message>
</context>
<context>
    <name>i18n</name>
    <message>
        <location filename="../i18n.py" line="+89"/>
        <source>System language</source>
        <translation>Systemsprache</translation>
    </message>
</context>
<context>
    <name>logger</name>
    <message>
        <location filename="../logger.py" line="+70"/>
        <source>Save Log File</source>
        <translation>Protokoll speichern</translation>
    </message>
</context>
<context>
    <name>update</name>
    <message>
        <location filename="../update.py" line="+69"/>
        <source>DANGER - you can ignore this warning by pressing OK</source>
        <translation>ACHTUNG – Sie können diese Warnung mit OK übergehen</translation>
    </message>
    <message>
        <location line="+8"/>
        <location line="+33"/>
        <location line="+32"/>
        <location line="+23"/>
        <location line="+15"/>
        <source>The firmware update was cancelled.</source>
        <translation>Das Firmware-Update wurde abgebrochen.</translation>
    </message>
    <message>
        <location line="-95"/>
        <source>The firmware image ({0}) is older than the firmware on the device ({1}).</source>
        <translation>Das Firmware-Abbild ({0}) ist älter als die Firmware auf dem Gerät ({1}).</translation>
    </message>
    <message>
        <location line="+18"/>
        <source>Do you want to download firmware version {0}?</source>
        <translation>Möchten Sie die Firmware-Version {0} herunterladen?</translation>
    </message>
    <message>
        <location line="+13"/>
        <source>{0} Firmware Update</source>
        <translation>{0} Firmware-Update</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>Please do not remove the {0} or insert any other {0} devices during the update. Doing so may damage the {0}.</source>
        <translation>Bitte entfernen Sie den {0} nicht und stecken Sie während des Updates keine weiteren {0}-Geräte ein. Das kann den {0} beschädigen.</translation>
    </message>
    <message>
        <location line="+7"/>
        <source>QubesOS is detected!

After the touch prompt, the {0} will be loaded into the bootloader. The Nitrokey must then be reattached to the current Qube.

Do you want to perform the firmware update now?</source>
        <translation>QubesOS wurde erkannt!

Nach der Berührungsaufforderung wird der {0} in den Bootloader geladen. Der Nitrokey muss dann erneut mit der aktuellen Qube verbunden werden.

Möchten Sie das Firmware-Update jetzt durchführen?</translation>
    </message>
    <message>
        <location line="+8"/>
        <source>Do you want to perform the firmware update now?</source>
        <translation>Möchten Sie das Firmware-Update jetzt durchführen?</translation>
    </message>
    <message>
        <location line="+16"/>
        <source>Device is in bootloader mode</source>
        <translation>Das Gerät ist im Bootloader-Modus</translation>
    </message>
    <message>
        <location line="+6"/>
        <source>The version of the firmware image is the same as the one on the device. Do you want to continue anyway?</source>
        <translation>Die Version des Firmware-Abbilds ist dieselbe wie auf dem Gerät. Möchten Sie trotzdem fortfahren?</translation>
    </message>
    <message>
        <location line="+19"/>
        <source>Confirm extra information</source>
        <translation>Zusätzliche Informationen bestätigen</translation>
    </message>
    <message>
        <location line="+19"/>
        <source>This version of the Nitrokey App is too old for the update. Please install version {0} or newer.</source>
        <translation>Diese Version der Nitrokey App ist zu alt für das Update. Bitte installieren Sie Version {0} oder neuer.</translation>
    </message>
    <message>
        <location line="+9"/>
        <source>The device was switched to bootloader mode. Please start the firmware update again.</source>
        <translation>Das Gerät wurde in den Bootloader-Modus versetzt. Bitte starten Sie das Firmware-Update erneut.</translation>
    </message>
    <message>
        <location line="+14"/>
        <source>Update</source>
        <translation>Update</translation>
    </message>
    <message>
        <location line="+5"/>
        <source>Download</source>
        <translation>Download</translation>
    </message>
    <message>
        <location line="+5"/>
        <source>Finalization</source>
        <translation>Abschluss</translation>
    </message>
    <message>
        <location line="+16"/>
        <source>The device is no longer available.</source>
        <translation>Das Gerät ist nicht mehr verfügbar.</translation>
    </message>
    <message>
        <location line="+5"/>
        <source>Found a {0} where a {1} was expected.</source>
        <translation>Es wurde ein {0} gefunden, erwartet wurde ein {1}.</translation>
    </message>
    <message>
        <location line="+30"/>
        <source>More than one {0} is connected. Please connect only the device that should be updated.</source>
        <translation>Es ist mehr als ein {0} angeschlossen. Bitte schließen Sie nur das Gerät an, das aktualisiert werden soll.</translation>
    </message>
    <message>
        <location line="+12"/>
        <source>The {0} could not be found.</source>
        <translation>Der {0} konnte nicht gefunden werden.</translation>
    </message>
    <message>
        <location line="+34"/>
        <source>The external filesystem of the device needs to be reformatted. Please contact {0} for more information on how to solve this issue.</source>
        <translation>Das externe Dateisystem des Geräts muss neu formatiert werden. Bitte wenden Sie sich an {0}, um zu erfahren, wie Sie das Problem lösen.</translation>
    </message>
</context>
<context>
    <name>utils</name>
    <message>
        <location filename="../utils.py" line="+87"/>
        <source>Missing Dependency</source>
        <translation>Fehlende Abhängigkeit</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>{0} is set but pyscard is not installed.
Please install it to use CCID mode.</source>
        <translation>{0} ist gesetzt, aber pyscard ist nicht installiert.
Bitte installieren Sie es, um den CCID-Modus zu nutzen.</translation>
    </message>
</context>
</TS>
