/*
 * File:     android/app/src/main/java/com/mrbacco/syndicate/data/model/Screens.kt
 * Author:   mrbacco04@gmail.com
 * GitHub:   https://github.com/mrbacco
 * Created:  2026-10-20
 * Updated:  2026-10-20
 * Project:  SYNDICATE
 * License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial
 */

package com.mrbacco.syndicate.data.model

import kotlinx.serialization.Serializable

// What the backend sends for each screen (backend/app/schemas.py). Everything is already worked
// out and worded on the server, so the app only displays it. Field names are converted from the
// server's snake_case automatically.

@Serializable
data class Syndicate(
    val id: String,
    val name: String,
    val weeklyCostCents: Int,
    val drawDays: List<String>,
)

@Serializable
data class SummaryCard(val title: String, val lines: List<String>)

// ------------------------------------------------------------ My syndicates

@Serializable
data class SyndicateRow(val id: String, val name: String, val subtitle: String)

@Serializable
data class SyndicateListScreen(val syndicates: List<SyndicateRow>)

// ------------------------------------------------------------------ Members

@Serializable
data class MemberRow(
    val id: String,
    val name: String,
    val phone: String? = null,
    /** International digits for WhatsApp links, e.g. "353871234567". */
    val whatsappNumber: String? = null,
    val paidThisWeek: Boolean,
    val weeksOwed: Int,
    val amountOwedCents: Int,
    /** "All paid up" or "Owes €5.00 (1 week)". */
    val status: String,
    /** Ready to send by SMS or WhatsApp; it includes [pageUrl]. */
    val message: String,
    /** The member's own web page, where they see their payments and the results. */
    val pageUrl: String? = null,
)

@Serializable
data class MembersScreen(
    val syndicate: Syndicate,
    /** The Monday of this week, e.g. "2026-10-19"; payments are recorded against it. */
    val weekStart: String,
    val summary: SummaryCard,
    val members: List<MemberRow>,
    val emptyText: String? = null,
)

// -------------------------------------------------------------------- Lines

@Serializable
data class LineRow(val id: String, val numbers: List<Int>)

@Serializable
data class LinesScreen(
    val syndicate: Syndicate,
    val summary: SummaryCard,
    val lines: List<LineRow>,
    val emptyText: String? = null,
)

// ------------------------------------------------------------------ Results

@Serializable
data class DrawCard(
    val drawDate: String,
    /** "Mon 19 Oct 2026". */
    val title: String,
    val numbers: List<Int>,
    val bonus: Int,
)

@Serializable
data class LineResultRow(
    val lineId: String,
    val numbers: List<Int>,
    val matched: List<Int>,
    val bonusMatched: Boolean,
    /** "Matched 3 numbers + bonus". */
    val text: String,
    /** "Match 3 + Bonus", or null if the line won nothing. */
    val prizeTier: String? = null,
    /** What that tier paid per line, e.g. "€25", once lottery.ie has published it. */
    val prizeAmount: String? = null,
    val won: Boolean,
)

@Serializable
data class ResultsScreen(
    val syndicate: Syndicate,
    val latestDraw: DrawCard? = null,
    val verdict: String? = null,
    val results: List<LineResultRow>,
    val previousDraws: List<DrawCard>,
    /** Who shares the latest draw's winnings and how much each gets; null if nothing was won. */
    val winnings: SummaryCard? = null,
    val emptyText: String? = null,
)

// -------------------------------------------------------------------- Rules

/** The Lotto rules today; the app checks typed lines against them before sending. */
@Serializable
data class GameRules(
    val name: String,
    val numbersPerLine: Int,
    val maxNumber: Int,
    val drawDayLabels: List<String>,
)

// ----------------------------------------------------------------- Requests

@Serializable
data class NewSyndicate(val name: String, val weeklyCostCents: Int)

@Serializable
data class NewMember(val name: String, val phone: String? = null)

/** Changes to a member. An empty [phone] removes the number. */
@Serializable
data class MemberChanges(val name: String, val phone: String)

@Serializable
data class LineNumbers(val numbers: List<Int>)
