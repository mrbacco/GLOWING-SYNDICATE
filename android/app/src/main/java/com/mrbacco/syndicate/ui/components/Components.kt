/*
 * File:     android/app/src/main/java/com/mrbacco/syndicate/ui/components/Components.kt
 * Author:   mrbacco04@gmail.com
 * GitHub:   https://github.com/mrbacco
 * Created:  2026-10-20
 * Updated:  2026-10-20
 * Project:  SYNDICATE
 * License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial
 */

package com.mrbacco.syndicate.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/** One lotto ball. Highlighted balls are numbers that matched the draw. */
@Composable
fun NumberBall(number: Int, highlighted: Boolean = false, bonus: Boolean = false) {
    val colors = MaterialTheme.colorScheme
    val background = when {
        bonus -> colors.secondaryContainer
        highlighted -> colors.primary
        else -> colors.surfaceVariant
    }
    val foreground = when {
        bonus -> colors.onSecondaryContainer
        highlighted -> colors.onPrimary
        else -> colors.onSurfaceVariant
    }
    Box(
        modifier = Modifier.size(34.dp).background(background, CircleShape),
        contentAlignment = Alignment.Center,
    ) {
        Text(number.toString(), color = foreground, fontWeight = FontWeight.Bold, fontSize = 14.sp)
    }
}

/** [matchedBonus] is a number in [numbers] that matched the draw's bonus ball; it gets the bonus colour. */
@Composable
fun BallRow(numbers: List<Int>, highlighted: Set<Int> = emptySet(), bonus: Int? = null, matchedBonus: Int? = null) {
    Row(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalAlignment = Alignment.CenterVertically) {
        numbers.forEach { NumberBall(it, highlighted = it in highlighted, bonus = it == matchedBonus) }
        if (bonus != null) {
            Text("+", style = MaterialTheme.typography.titleMedium)
            NumberBall(bonus, bonus = true)
        }
    }
}

/**
 * A dialog with text fields. [validate] gets the current values and returns an
 * error message, or null when the input is fine and [onConfirm] may be called.
 * With [onDelete], it also shows a Delete button, for editing something that exists.
 */
@Composable
fun InputDialog(
    title: String,
    labels: List<String>,
    confirmText: String = "Add",
    initialValues: List<String> = List(labels.size) { "" },
    validate: (List<String>) -> String?,
    onConfirm: (List<String>) -> Unit,
    onDismiss: () -> Unit,
    onDelete: (() -> Unit)? = null,
) {
    var values by rememberSaveable { mutableStateOf(initialValues) }
    var error by rememberSaveable { mutableStateOf<String?>(null) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(title) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                labels.forEachIndexed { index, label ->
                    OutlinedTextField(
                        value = values[index],
                        onValueChange = { new ->
                            values = values.toMutableList().also { it[index] = new }
                            error = null
                        },
                        label = { Text(label) },
                        singleLine = true,
                    )
                }
                error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            }
        },
        confirmButton = {
            TextButton(onClick = {
                val problem = validate(values)
                if (problem == null) onConfirm(values) else error = problem
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

/** Asks "are you sure?" before something that cannot be undone, such as deleting. */
@Composable
fun ConfirmDialog(
    title: String,
    text: String,
    confirmText: String,
    onConfirm: () -> Unit,
    onDismiss: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(title) },
        text = { Text(text) },
        confirmButton = {
            TextButton(onClick = onConfirm) { Text(confirmText, color = MaterialTheme.colorScheme.error) }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel") } },
    )
}
