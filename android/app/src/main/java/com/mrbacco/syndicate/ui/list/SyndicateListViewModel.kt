/*
 * File:     android/app/src/main/java/com/mrbacco/syndicate/ui/list/SyndicateListViewModel.kt
 * Author:   mrbacco04@gmail.com
 * GitHub:   https://github.com/mrbacco
 * Created:  2026-10-20
 * Updated:  2026-10-20
 * Project:  SYNDICATE
 * License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial
 */

package com.mrbacco.syndicate.ui.list

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.mrbacco.syndicate.data.ApiException
import com.mrbacco.syndicate.data.SyndicateRepository
import com.mrbacco.syndicate.data.model.SyndicateListScreen
import com.mrbacco.syndicate.ui.components.Loadable
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class SyndicateListViewModel(private val repository: SyndicateRepository) : ViewModel() {

    private val _state = MutableStateFlow<Loadable<SyndicateListScreen>>(Loadable.Loading)
    val state: StateFlow<Loadable<SyndicateListScreen>> = _state.asStateFlow()

    /** A one-off message for a snackbar, e.g. when saving failed. */
    private val _message = MutableStateFlow<String?>(null)
    val message: StateFlow<String?> = _message.asStateFlow()

    fun refresh() {
        viewModelScope.launch { reload() }
    }

    fun addSyndicate(name: String, weeklyCostCents: Int) {
        viewModelScope.launch {
            try {
                repository.addSyndicate(name, weeklyCostCents)
                reload()
            } catch (e: ApiException) {
                _message.value = e.message
            }
        }
    }

    fun messageShown() {
        _message.value = null
    }

    private suspend fun reload() {
        try {
            _state.value = Loadable.Ready(repository.syndicateList())
        } catch (e: ApiException) {
            // Keep showing what we have; only an empty screen turns into the error screen.
            if (_state.value is Loadable.Ready) _message.value = e.message
            else _state.value = Loadable.Failed(e.message.orEmpty())
        }
    }
}
