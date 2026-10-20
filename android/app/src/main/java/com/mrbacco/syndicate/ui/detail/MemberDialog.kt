/*
 * File:     android/app/src/main/java/com/mrbacco/syndicate/ui/detail/MemberDialog.kt
 * Author:   mrbacco04@gmail.com
 * GitHub:   https://github.com/mrbacco
 * Created:  2026-10-20
 * Updated:  2026-10-20
 * Project:  SYNDICATE
 * License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial
 */

package com.mrbacco.syndicate.ui.detail

import android.Manifest
import android.app.Activity
import android.content.ContentProviderOperation
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.provider.ContactsContract
import android.provider.ContactsContract.CommonDataKinds.Phone
import android.provider.ContactsContract.CommonDataKinds.StructuredName
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContract
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Checkbox
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import com.mrbacco.syndicate.domain.PhoneNumbers
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * Asks for a member's name and mobile number, to add a member or (with [initialName] and
 * [onDelete]) to edit one. The number can be picked from the phone's contacts (no permission
 * needed: the picker grants access to the chosen contact only), or typed in and saved as a new
 * phone contact (asks for the contacts permission the first time).
 */
@Composable
fun MemberDialog(
    onConfirm: (name: String, phone: String?) -> Unit,
    onDismiss: () -> Unit,
    title: String = "Add member",
    confirmText: String = "Add",
    initialName: String = "",
    initialPhone: String = "",
    onDelete: (() -> Unit)? = null,
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var name by rememberSaveable { mutableStateOf(initialName) }
    var phone by rememberSaveable { mutableStateOf(initialPhone) }
    var pickedFromContacts by rememberSaveable { mutableStateOf(false) }
    var saveToContacts by rememberSaveable { mutableStateOf(true) }
    var error by rememberSaveable { mutableStateOf<String?>(null) }

    fun finish(saveContact: Boolean) {
        val trimmedName = name.trim()
        val trimmedPhone = phone.trim().ifEmpty { null }
        if (saveContact && trimmedPhone != null) {
            // Close the dialog only after saving: closing it cancels this scope.
            scope.launch {
                val saved = withContext(Dispatchers.IO) { saveContact(context, trimmedName, trimmedPhone) }
                val message = if (saved) "Saved $trimmedName to your contacts" else "Could not save the contact"
                Toast.makeText(context, message, Toast.LENGTH_SHORT).show()
                onConfirm(trimmedName, trimmedPhone)
            }
        } else {
            onConfirm(trimmedName, trimmedPhone)
        }
    }

    val pickContact = rememberLauncherForActivityResult(PickPhoneContact()) { uri ->
        val contact = uri?.let { readContact(context, it) } ?: return@rememberLauncherForActivityResult
        name = contact.first
        phone = contact.second
        pickedFromContacts = true
        error = null
    }
    val requestPermission = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (!granted) Toast.makeText(context, "Saved without adding to your contacts", Toast.LENGTH_SHORT).show()
        finish(saveContact = granted)
    }

    // Only offer to save a number that is new: not picked from contacts, not the one it already had.
    val showSaveOption = phone.isNotBlank() && !pickedFromContacts && phone.trim() != initialPhone.trim()

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(title) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(onClick = { pickContact.launch(Unit) }) { Text("Pick from contacts") }
                OutlinedTextField(
                    value = name,
                    onValueChange = { name = it; error = null },
                    label = { Text("Name") },
                    singleLine = true,
                )
                OutlinedTextField(
                    value = phone,
                    onValueChange = { phone = it; pickedFromContacts = false; error = null },
                    label = { Text("Mobile number (optional)") },
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone),
                )
                if (showSaveOption) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Checkbox(checked = saveToContacts, onCheckedChange = { saveToContacts = it })
                        Text("Save to phone contacts")
                    }
                }
                error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            }
        },
        confirmButton = {
            TextButton(onClick = {
                error = when {
                    name.isBlank() -> "Please enter a name."
                    phone.isNotBlank() && PhoneNumbers.international(phone) == null -> "That doesn't look like a phone number."
                    else -> null
                }
                if (error != null) return@TextButton
                val wantsSave = showSaveOption && saveToContacts
                val hasPermission = ContextCompat.checkSelfPermission(context, Manifest.permission.WRITE_CONTACTS) ==
                    PackageManager.PERMISSION_GRANTED
                if (wantsSave && !hasPermission) requestPermission.launch(Manifest.permission.WRITE_CONTACTS)
                else finish(saveContact = wantsSave)
            }) { Text(confirmText) }
        },
        dismissButton = {
            Row {
                onDelete?.let { delete ->
                    TextButton(onClick = delete) { Text("Delete", color = MaterialTheme.colorScheme.error) }
                }
                TextButton(onClick = onDismiss) { Text("Cancel") }
            }
        },
    )
}

/** Opens the phone's contact picker, showing only contacts that have a phone number. */
private class PickPhoneContact : ActivityResultContract<Unit, Uri?>() {
    override fun createIntent(context: Context, input: Unit) = Intent(Intent.ACTION_PICK, Phone.CONTENT_URI)
    override fun parseResult(resultCode: Int, intent: Intent?): Uri? =
        intent?.data.takeIf { resultCode == Activity.RESULT_OK }
}

/** Name and number of the picked contact, or null if it could not be read. */
private fun readContact(context: Context, uri: Uri): Pair<String, String>? =
    context.contentResolver.query(uri, arrayOf(Phone.DISPLAY_NAME, Phone.NUMBER), null, null, null)?.use { cursor ->
        if (cursor.moveToFirst()) cursor.getString(0).orEmpty() to cursor.getString(1).orEmpty() else null
    }

/** Saves a new contact with a mobile number on the phone. Returns false if it failed. */
private fun saveContact(context: Context, name: String, phone: String): Boolean {
    val ops = arrayListOf(
        ContentProviderOperation.newInsert(ContactsContract.RawContacts.CONTENT_URI)
            .withValue(ContactsContract.RawContacts.ACCOUNT_TYPE, null)
            .withValue(ContactsContract.RawContacts.ACCOUNT_NAME, null)
            .build(),
        ContentProviderOperation.newInsert(ContactsContract.Data.CONTENT_URI)
            .withValueBackReference(ContactsContract.Data.RAW_CONTACT_ID, 0)
            .withValue(ContactsContract.Data.MIMETYPE, StructuredName.CONTENT_ITEM_TYPE)
            .withValue(StructuredName.DISPLAY_NAME, name)
            .build(),
        ContentProviderOperation.newInsert(ContactsContract.Data.CONTENT_URI)
            .withValueBackReference(ContactsContract.Data.RAW_CONTACT_ID, 0)
            .withValue(ContactsContract.Data.MIMETYPE, Phone.CONTENT_ITEM_TYPE)
            .withValue(Phone.NUMBER, phone)
            .withValue(Phone.TYPE, Phone.TYPE_MOBILE)
            .build(),
    )
    return runCatching { context.contentResolver.applyBatch(ContactsContract.AUTHORITY, ops) }.isSuccess
}
