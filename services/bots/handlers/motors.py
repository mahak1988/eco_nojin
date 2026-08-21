"""Scientific Motors Bot Handlers."""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router(name="motors_bot")


@router.message(Command("motors"))
async def cmd_motors(message: Message):
    """List available scientific motors."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💧 SWAT+", callback_data="motor:swat_plus"),
            InlineKeyboardButton(text="🌾 AquaCrop", callback_data="motor:aquacrop"),
        ],
        [
            InlineKeyboardButton(text="🌍 RothC", callback_data="motor:rothc"),
            InlineKeyboardButton(text="🌊 HEC-RAS", callback_data="motor:hecras"),
        ],
        [
            InlineKeyboardButton(text="🎲 What-If", callback_data="motor:what_if"),
        ],
    ])

    await message.answer(
        "🔬 **Scientific Motors**\n\n"
        "Select a motor to run:\n\n"
        "💧 **SWAT+**: Water balance simulation\n"
        "🌾 **AquaCrop**: Crop yield prediction\n"
        "🌍 **RothC**: Soil carbon dynamics\n"
        "🌊 **HEC-RAS**: Flood routing\n"
        "🎲 **What-If**: Scenario analysis",
        reply_markup=keyboard,
    )


@router.message(Command("map"))
async def cmd_map(message: Message):
    """Generate a map."""
    await message.answer(
        "🗺️ **Map Generation**\n\n"
        "Available map types:\n"
        "- M-TOP: Topographic\n"
        "- M-SLP: Slope & Aspect\n"
        "- M-ERS: RUSLE Erosion\n"
        "- M-VEG: Vegetation Indices\n"
        "- M-RUN: SCS-CN Runoff\n\n"
        "Use /generate <map_type> to generate a map."
    )


@router.message(Command("mrv"))
async def cmd_mrv(message: Message):
    """Start MRV observation."""
    await message.answer(
        "📋 **MRV Observation**\n\n"
        "Please provide:\n"
        "1. Location (or send location)\n"
        "2. Observation type (soil, yield, biomass)\n"
        "3. Photo evidence\n"
        "4. Notes\n\n"
        "Start by sending your location."
    )


@router.message(Command("report"))
async def cmd_report(message: Message):
    """Generate PDF report."""
    await message.answer(
        "📄 **Report Generation**\n\n"
        "Generating PDF report...\n"
        "This may take a few minutes."
    )