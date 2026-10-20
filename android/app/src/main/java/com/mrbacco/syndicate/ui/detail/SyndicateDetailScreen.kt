/*
 * File:     android/app/src/main/java/com/mrbacco/syndicate/ui/detail/SyndicateDetailScreen.kt
 * Author:   mrbacco04@gmail.com
 * GitHub:   https://github.com/mrbacco
 * Created:  2026-10-20
 * Updated:  2026-10-20
 * Project:  SYNDICATE
 * License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial
 */

package com.mrbacco.syndicate.ui.detail

import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.widget.Toast
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyListScope
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Checkbox
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.mrbacco.syndicate.data.AppContainer
import com.mrbacco.syndicate.data.model.DrawCard
import com.mrbacco.syndicate.data.model.LinesScreen
import com.mrbacco.syndicate.data.model.MemberRow
import com.mrbacco.syndicate.data.model.MembersScreen
import com.mrbacco.syndicate.data.model.ResultsScreen
import com.mrbacco.syndicate.data.model.SummaryCard
import com.mrbacco.syndicate.domain.LineInput
import com.mrbacco.syndicate.domain.PhoneNumbers
import com.mrbacco.syndicate.ui.components.BallRow
import com.mrbacco.syndicate.ui.components.ConfirmDialog
import com.mrbacco.syndicate.ui.components.InputDialog
import com.mrbacco.syndicate.ui.components.Loadable
import com.mrbacco.syndicate.ui.components.LoadableContent

private enum class DetailTab(val title: String) { MEMBERS("Members"), LINES("Lines"), RESULTS("Results") }

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SyndicateDetailScreen(
    syndicateId: String,
    onBack: () -> Unit,
    viewModel: SyndicateDetailViewModel = viewModel(key = syndicateId) {
        SyndicateDetailViewModel(syndicateId, AppContainer.repository)
    },
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val message by viewModel.message.collectAsStateWithLifecycle()
    val snackbar = remember { SnackbarHostState() }
    var tab by rememberSaveable { mutableIntStateOf(0) }
    var showAddMember by rememberSaveable { mutableStateOf(false) }
    var showAddLine by rememberSaveable { mutableStateOf(false) }
    // Ids of the member or line being edited, or waiting for "are you sure?" before deleting.
    var editingMemberId by rememberSaveable { mutableStateOf<String?>(null) }
    var deletingMemberId by rememberSaveable { mutableStateOf<String?>(null) }
    var editingLineId by rememberSaveable { mutableStateOf<String?>(null) }
    var deletingLineId by rememberSaveable { mutableStateOf<String?>(null) }
    val currentTab = DetailTab.entries[tab]
    val data = (state as? Loadable.Ready)?.value

    LaunchedEffect(message) {
        message?.let {
            snackbar.showSnackbar(it)
            viewModel.messageShown()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(data?.syndicateName.orEmpty()) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    IconButton(onClick = viewModel::refresh) {
                        Icon(Icons.Filled.Refresh, contentDescription = "Refresh")
                    }
                },
            )
        },
        snackbarHost = { SnackbarHost(snackbar) },
        floatingActionButton = {
            if (data != null) {
                when (currentTab) {
                    DetailTab.MEMBERS -> FloatingActionButton(onClick = { showAddMember = true }) {
                        Icon(Icons.Filled.Add, contentDescription = "Add member")
                    }
                    DetailTab.LINES -> FloatingActionButton(onClick = { showAddLine = true }) {
                        Icon(Icons.Filled.Add, contentDescription = "Add line")
                    }
                    DetailTab.RESULTS -> Unit
                }
            }
        },
    ) { padding ->
        LoadableContent(state, onRetry = viewModel::refresh, modifier = Modifier.padding(padding)) { current ->
            Column(Modifier.fillMaxSize().padding(padding)) {
                TabRow(selectedTabIndex = tab) {
                    DetailTab.entries.forEachIndexed { index, item ->
                        Tab(selected = tab == index, onClick = { tab = index }, text = { Text(item.title) })
                    }
                }
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    when (currentTab) {
                        DetailTab.MEMBERS -> membersTab(current.members, viewModel::setPaid) { editingMemberId = it }
                        DetailTab.LINES -> linesTab(current.lines) { editingLineId = it }
                        DetailTab.RESULTS -> resultsTab(current.results)
                    }
                }
            }
        }
    }

    if (showAddMember) {
        MemberDialog(
            onConfirm = { name, phone ->
                viewModel.addMember(name, phone)
                showAddMember = false
            },
            onDismiss = { showAddMember = false },
        )
    }
    data?.members?.members?.find { it.id == editingMemberId }?.let { member ->
        MemberDialog(
            title = "Edit member",
            confirmText = "Save",
            initialName = member.name,
            initialPhone = member.phone.orEmpty(),
            onConfirm = { name, phone ->
                viewModel.updateMember(member.id, name, phone)
                editingMemberId = null
            },
            onDismiss = { editingMemberId = null },
            onDelete = {
                deletingMemberId = member.id
                editingMemberId = null
            },
        )
    }
    data?.members?.members?.find { it.id == deletingMemberId }?.let { member ->
        ConfirmDialog(
            title = "Remove ${member.name}?",
            text = "This also deletes their payment history for this syndicate. It can't be undone.",
            confirmText = "Remove",
            onConfirm = {
                viewModel.deleteMember(member.id, member.name)
                deletingMemberId = null
            },
            onDismiss = { deletingMemberId = null },
        )
    }

    val rules = data?.rules
    if (rules != null) {
        val count = rules.numbersPerLine
        val max = rules.maxNumber
        val label = "$count numbers, e.g. 3 12 24 27 38 41"
        val validate = { values: List<String> ->
            if (LineInput.parse(values[0], count, max) == null) "Enter $count different numbers from 1 to $max." else null
        }
        if (showAddLine) {
            InputDialog(
                title = "Add line",
                labels = listOf(label),
                validate = validate,
                onConfirm = { (text) ->
                    viewModel.addLine(LineInput.parse(text, count, max)!!)
                    showAddLine = false
                },
                onDismiss = { showAddLine = false },
            )
        }
        data.lines.lines.find { it.id == editingLineId }?.let { line ->
            InputDialog(
                title = "Edit line",
                labels = listOf(label),
                confirmText = "Save",
                initialValues = listOf(line.numbers.joinToString(" ")),
                validate = validate,
                onConfirm = { (text) ->
                    viewModel.updateLine(line.id, LineInput.parse(text, count, max)!!)
                    editingLineId = null
                },
                onDismiss = { editingLineId = null },
                onDelete = {
                    deletingLineId = line.id
                    editingLineId = null
                },
            )
        }
    }
    data?.lines?.lines?.find { it.id == deletingLineId }?.let { line ->
        ConfirmDialog(
            title = "Delete this line?",
            text = "${line.numbers.joinToString(" ")} will no longer be checked against the draws.",
            confirmText = "Delete",
            onConfirm = {
                viewModel.deleteLine(line.id)
                deletingLineId = null
            },
            onDismiss = { deletingLineId = null },
        )
    }
}

// ---------------------------------------------------------------- Members tab

private fun LazyListScope.membersTab(
    screen: MembersScreen,
    onPaidChange: (String, Boolean) -> Unit,
    onEdit: (String) -> Unit,
) {
    item { SummaryCard(screen.summary) }
    screen.emptyText?.let { item { Text(it) } }
    items(screen.members, key = { it.id }) { row -> MemberCard(row, onPaidChange, onClick = { onEdit(row.id) }) }
}

/** Tapping the card opens the member for editing; the buttons and the checkbox act on their own. */
@Composable
private fun MemberCard(row: MemberRow, onPaidChange: (String, Boolean) -> Unit, onClick: () -> Unit) {
    val context = LocalContext.current
    Card(onClick = onClick, modifier = Modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier.padding(start = 16.dp, end = 8.dp, top = 8.dp, bottom = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f)) {
                Text(row.name, style = MaterialTheme.typography.titleMedium)
                Text(
                    row.status,
                    color = if (row.weeksOwed == 0) MaterialTheme.colorScheme.primary
                    else MaterialTheme.colorScheme.onSurfaceVariant,
                    fontWeight = FontWeight.Bold,
                )
                val phone = row.phone
                if (phone == null) {
                    // The server's message carries the member's page link either way.
                    TextButton(
                        onClick = { shareReminder(context, row.message) },
                        contentPadding = PaddingValues(0.dp),
                    ) { Text(if (row.weeksOwed > 0) "Send reminder" else "Send page link") }
                } else {
                    Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                        TextButton(
                            onClick = { openSms(context, phone, row.message) },
                            contentPadding = PaddingValues(0.dp),
                        ) { Text("Send SMS") }
                        TextButton(
                            onClick = { openWhatsApp(context, row.whatsappNumber ?: PhoneNumbers.international(phone), row.message) },
                            contentPadding = PaddingValues(0.dp),
                        ) { Text("WhatsApp") }
                    }
                }
            }
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Checkbox(
                    checked = row.paidThisWeek,
                    onCheckedChange = { onPaidChange(row.id, it) },
                )
                Text("Paid", style = MaterialTheme.typography.labelSmall)
            }
        }
    }
}

/** Opens the share sheet (WhatsApp, SMS, ...) with [text], for members without a number. */
private fun shareReminder(context: Context, text: String) = shareText(context, text, "Send reminder")

/** Opens the share sheet with [text], e.g. to post in the syndicate's WhatsApp group. */
private fun shareText(context: Context, text: String, title: String) {
    val send = Intent(Intent.ACTION_SEND).apply {
        type = "text/plain"
        putExtra(Intent.EXTRA_TEXT, text)
    }
    context.startActivity(Intent.createChooser(send, title))
}

/** Opens the SMS app on a conversation with [phone], with [text] ready to send. */
private fun openSms(context: Context, phone: String, text: String) {
    val sms = Intent(Intent.ACTION_SENDTO, Uri.parse("smsto:" + Uri.encode(phone))).putExtra("sms_body", text)
    startOrToast(context, sms, "No SMS app found")
}

/** Opens a WhatsApp chat with [number] (international digits), with [text] ready to send. */
private fun openWhatsApp(context: Context, number: String?, text: String) {
    if (number == null) {
        Toast.makeText(context, "Can't open WhatsApp for this number", Toast.LENGTH_SHORT).show()
        return
    }
    val chat = Intent(Intent.ACTION_VIEW, Uri.parse("https://wa.me/$number?text=" + Uri.encode(text)))
    startOrToast(context, chat, "WhatsApp is not installed")
}

private fun startOrToast(context: Context, intent: Intent, problem: String) {
    try {
        context.startActivity(intent)
    } catch (e: ActivityNotFoundException) {
        Toast.makeText(context, problem, Toast.LENGTH_SHORT).show()
    }
}

// ------------------------------------------------------------------ Lines tab

/** Tapping a line opens it for editing. */
private fun LazyListScope.linesTab(screen: LinesScreen, onEdit: (String) -> Unit) {
    item { SummaryCard(screen.summary) }
    screen.emptyText?.let { item { Text(it) } }
    items(screen.lines, key = { it.id }) { line ->
        Card(onClick = { onEdit(line.id) }, modifier = Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp)) { BallRow(line.numbers) }
        }
    }
}

// ---------------------------------------------------------------- Results tab

private fun LazyListScope.resultsTab(screen: ResultsScreen) {
    val latest = screen.latestDraw
    if (latest == null) {
        item { Text(screen.emptyText.orEmpty()) }
        return
    }
    item {
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer),
        ) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Latest draw · ${latest.title}", style = MaterialTheme.typography.titleMedium)
                BallRow(latest.numbers, bonus = latest.bonus)
                screen.verdict?.let { Text(it, style = MaterialTheme.typography.bodyLarge) }
                screen.groupMessage?.let { message ->
                    val context = LocalContext.current
                    Button(onClick = { shareText(context, message, "Message the group") }) {
                        Text("Message the group")
                    }
                }
            }
        }
    }
    screen.winnings?.let { card -> item { SummaryCard(card) } }
    items(screen.results, key = { it.lineId }) { result ->
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                BallRow(
                    result.numbers,
                    highlighted = result.matched.toSet(),
                    matchedBonus = latest.bonus.takeIf { result.bonusMatched },
                )
                Text(
                    result.text,
                    color = if (result.won) MaterialTheme.colorScheme.primary
                    else MaterialTheme.colorScheme.onSurfaceVariant,
                )
                result.prizeTier?.let { tier ->
                    Text(
                        "Prize tier: $tier" + result.prizeAmount?.let { " · $it" }.orEmpty(),
                        style = MaterialTheme.typography.titleSmall,
                        color = MaterialTheme.colorScheme.primary,
                    )
                }
            }
        }
    }
    if (screen.previousDraws.isNotEmpty()) {
        item {
            Spacer(Modifier.padding(4.dp))
            Text("Previous draws", style = MaterialTheme.typography.titleMedium)
        }
        items(screen.previousDraws, key = { it.drawDate }) { draw -> PreviousDraw(draw) }
    }
}

@Composable
private fun PreviousDraw(draw: DrawCard) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(draw.title, style = MaterialTheme.typography.labelLarge)
        BallRow(draw.numbers, bonus = draw.bonus)
    }
}

// ------------------------------------------------------------------- Shared

@Composable
private fun SummaryCard(card: SummaryCard) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer),
    ) {
        Column(Modifier.padding(16.dp)) {
            Text(card.title, style = MaterialTheme.typography.titleMedium)
            card.lines.forEach { Text(it) }
        }
    }
}
