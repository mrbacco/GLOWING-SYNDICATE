/*
 * File:     android/app/src/main/java/com/mrbacco/syndicate/ui/list/SyndicateListScreen.kt
 * Author:   mrbacco04@gmail.com
 * GitHub:   https://github.com/mrbacco
 * Created:  2026-10-20
 * Updated:  2026-10-20
 * Project:  SYNDICATE
 * License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial
 */

package com.mrbacco.syndicate.ui.list

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.mrbacco.syndicate.data.AppContainer
import com.mrbacco.syndicate.data.model.SyndicateRow
import com.mrbacco.syndicate.domain.Money
import com.mrbacco.syndicate.ui.components.InputDialog
import com.mrbacco.syndicate.ui.components.LoadableContent

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SyndicateListScreen(
    onOpen: (String) -> Unit,
    viewModel: SyndicateListViewModel = viewModel { SyndicateListViewModel(AppContainer.repository) },
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val message by viewModel.message.collectAsStateWithLifecycle()
    val snackbar = remember { SnackbarHostState() }
    var showAdd by rememberSaveable { mutableStateOf(false) }

    // Reload every time the list is shown, e.g. when coming back from a syndicate.
    LaunchedEffect(Unit) { viewModel.refresh() }
    LaunchedEffect(message) {
        message?.let {
            snackbar.showSnackbar(it)
            viewModel.messageShown()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("My syndicates") },
                actions = {
                    IconButton(onClick = viewModel::refresh) {
                        Icon(Icons.Filled.Refresh, contentDescription = "Refresh")
                    }
                },
            )
        },
        snackbarHost = { SnackbarHost(snackbar) },
        floatingActionButton = {
            FloatingActionButton(onClick = { showAdd = true }) {
                Icon(Icons.Filled.Add, contentDescription = "New syndicate")
            }
        },
    ) { padding ->
        LoadableContent(state, onRetry = viewModel::refresh, modifier = Modifier.padding(padding)) { screen ->
            if (screen.syndicates.isEmpty()) {
                Box(Modifier.fillMaxSize().padding(padding), contentAlignment = Alignment.Center) {
                    Text("No syndicates yet. Tap + to create one.")
                }
            } else {
                LazyColumn(
                    modifier = Modifier.fillMaxSize().padding(padding),
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    items(screen.syndicates, key = { it.id }) { syndicate ->
                        SyndicateCard(syndicate, onClick = { onOpen(syndicate.id) })
                    }
                }
            }
        }
    }

    if (showAdd) {
        InputDialog(
            title = "New syndicate",
            labels = listOf("Name", "Cost per member per week (€)"),
            validate = { (name, cost) ->
                when {
                    name.isBlank() -> "Please enter a name."
                    Money.parseEuro(cost) == null -> "Please enter an amount like 2 or 2.50."
                    else -> null
                }
            },
            onConfirm = { (name, cost) ->
                viewModel.addSyndicate(name, Money.parseEuro(cost)!!)
                showAdd = false
            },
            onDismiss = { showAdd = false },
        )
    }
}

@Composable
private fun SyndicateCard(syndicate: SyndicateRow, onClick: () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth().clickable(onClick = onClick)) {
        Column(Modifier.padding(16.dp)) {
            Text(syndicate.name, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
            Text(
                syndicate.subtitle,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}
