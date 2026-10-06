# ============================================================
# JARVIS PERSONAL AI ASSISTANT (MARK VII)
# Main Entry Point & Holographic CLI Interface
# ============================================================

import argparse
import time

from rich.console import Console

import ai_interpreter
import jarvis_hud

from config import (
    BUTLER_NAME,
    OLLAMA_MODEL,
    USER_TITLE,
)

from tool_router import (
    execute,
    initialize,
)

from speech_engine import (
    speak,
    listen_for_command,
    is_voice_enabled,
)


console = Console()


# ============================================================
# VOICE INPUT
# ============================================================

def handle_voice_listen_mode():
    """
    Push-to-talk voice recognition session.
    """

    console.print(
        "\n[bold cyan]🎙️ JARVIS EAR ACTIVATED[/bold cyan] "
        "— [italic bright_white]"
        "Speak into your microphone now..."
        "[/italic bright_white]"
    )

    # Only speak if voice is enabled.
    if is_voice_enabled():
        speak(f"Listening, {USER_TITLE}.")

    text, error = listen_for_command(
        prompt_callback=lambda msg:
        console.print(
            f"[dim cyan]• {msg}[/dim cyan]"
        )
    )

    # --------------------------------------------------------
    # Voice error
    # --------------------------------------------------------

    if error:

        console.print(
            f"[bold yellow]⚠️ Voice Input Notice: "
            f"{error}[/bold yellow]"
        )

        if is_voice_enabled():
            speak(
                f"Pardon me {USER_TITLE}, "
                f"I could not hear you."
            )

        return None

    # --------------------------------------------------------
    # Successful voice input
    # --------------------------------------------------------

    if text:

        console.print(
            "[bold cyan]You (Voice) >[/bold cyan] "
            f"[bold bright_white]{text}[/bold bright_white]"
        )

        return text.strip()

    return None


# ============================================================
# COMMAND PROCESSING
# ============================================================

def run_command_cycle(command_text: str):
    """
    Process a single command through:

        User
          ↓
        Llama
          ↓
        Interpreter
          ↓
        Tool Router
          ↓
        Windows / Files / Web

    Returns:
        True  -> continue running
        False -> shutdown requested
    """

    command_text = command_text.strip()

    if not command_text:
        return True


    # ========================================================
    # DIRECT UI COMMANDS
    # ========================================================

    cmd_lower = command_text.lower()


    # --------------------------------------------------------
    # HELP
    # --------------------------------------------------------

    if cmd_lower in [
        "help",
        "commands",
        "manual",
        "?",
    ]:

        jarvis_hud.print_help()

        return True


    # --------------------------------------------------------
    # CLEAR SCREEN
    # --------------------------------------------------------

    if cmd_lower in [
        "clear",
        "cls",
    ]:

        console.clear()

        jarvis_hud.print_banner(
            model_name=OLLAMA_MODEL,
            voice_enabled=is_voice_enabled()
        )

        return True


    # ========================================================
    # VOICE TOGGLE
    # ========================================================

    if cmd_lower in [
        "voice off",
        "mute voice",
        "mute",
    ]:

        result = execute({
            "action": "set_voice",
            "enabled": False
        })

        console.print(
            f"[bold yellow]🔇 "
            f"{result.get('message', 'Voice disabled.')} "
            f"[/bold yellow]"
        )

        return True


    if cmd_lower in [
        "voice on",
        "unmute voice",
        "unmute",
    ]:

        result = execute({
            "action": "set_voice",
            "enabled": True
        })

        console.print(
            f"[bold green]🔊 "
            f"{result.get('message', 'Voice enabled.')} "
            f"[/bold green]"
        )

        if is_voice_enabled():

            speak(
                f"Voice synthesis online, "
                f"{USER_TITLE}."
            )

        return True


    # ========================================================
    # INTERPRET COMMAND WITH LLAMA
    # ========================================================

    try:

        interpreted = ai_interpreter.interpret(
            command_text
        )

    except Exception as error:

        console.print(
            "\n[bold red]⚠️ AI Interpreter Error:[/bold red]"
        )

        console.print(
            f"[red]{error}[/red]\n"
        )

        if is_voice_enabled():

            speak(
                f"I encountered an interpreter error, "
                f"{USER_TITLE}."
            )

        return True


    # ========================================================
    # DEBUG / HUD
    # ========================================================

    console.print(
        f"[dim cyan]Neural directive:[/dim cyan] "
        f"[dim white]{interpreted}[/dim white]"
    )


    # ========================================================
    # EXIT
    # ========================================================

    if interpreted.get("action") == "exit":

        farewell = (
            "Powering down auxiliary systems. "
            f"Have a pleasant day, {USER_TITLE}."
        )

        jarvis_hud.print_jarvis_response(
            farewell,
            title="SYSTEM SHUTDOWN"
        )

        if is_voice_enabled():

            speak(
                farewell,
                wait=True
            )

        return False


    # ========================================================
    # UNKNOWN COMMAND
    # ========================================================

    if interpreted.get("action") == "unknown":

        message = (
            "I don't understand that directive yet."
        )

        jarvis_hud.print_jarvis_response(
            message,
            title=BUTLER_NAME
        )

        if is_voice_enabled():

            speak(message)

        return True


    # ========================================================
    # EXECUTE TOOL
    # ========================================================

    try:

        result = execute(interpreted)

    except Exception as error:

        console.print(
            "\n[bold red]⚠️ Tool execution error:[/bold red]"
        )

        console.print(
            f"[red]{error}[/red]\n"
        )

        if is_voice_enabled():

            speak(
                f"I encountered an execution error, "
                f"{USER_TITLE}."
            )

        return True


    # ========================================================
    # RESULT HANDLING
    # ========================================================

    action = interpreted.get("action")


    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    if result.get("success"):

        # ----------------------------------------------------
        # System status
        # ----------------------------------------------------

        if (
            action == "system_status"
            and "stats" in result
        ):

            jarvis_hud.print_system_dashboard(
                result["stats"]
            )


        # ----------------------------------------------------
        # Weather
        # ----------------------------------------------------

        elif (
            action == "weather"
            and "weather" in result
        ):

            jarvis_hud.print_weather_card(
                result["weather"]
            )


        # ----------------------------------------------------
        # News
        # ----------------------------------------------------

        elif (
            action == "news"
            and "news" in result
        ):

            jarvis_hud.print_news_feed(
                result["news"],
                category=interpreted.get(
                    "category",
                    "Technology"
                )
            )


        # ----------------------------------------------------
        # Notes
        # ----------------------------------------------------

        elif (
            action == "list_notes"
            and "notes" in result
        ):

            jarvis_hud.print_notes_table(
                result["notes"]
            )


        # ----------------------------------------------------
        # File results
        # ----------------------------------------------------

        elif action in [
            "list_files",
            "search_files",
            "search_file_content",
        ]:

            message = result.get("message")

            if message:

                jarvis_hud.print_jarvis_response(
                    message,
                    title=BUTLER_NAME
                )

            # Display returned file information.
            if "files" in result:

                console.print(
                    "\n[bold cyan]FILES[/bold cyan]"
                )

                for file_path in result["files"]:

                    console.print(
                        f"[dim]•[/dim] {file_path}"
                    )

            if "results" in result:

                console.print(
                    "\n[bold cyan]SEARCH RESULTS[/bold cyan]"
                )

                for item in result["results"]:

                    if isinstance(item, dict):

                        console.print(
                            f"[dim]•[/dim] "
                            f"{item.get('file', item)}"
                        )

                    else:

                        console.print(
                            f"[dim]•[/dim] {item}"
                        )


        # ----------------------------------------------------
        # File contents
        # ----------------------------------------------------

        elif action == "read_file":

            path = result.get(
                "path",
                "Unknown file"
            )

            content = result.get(
                "content",
                ""
            )

            console.print(
                f"\n[bold cyan]FILE:[/bold cyan] "
                f"{path}"
            )

            console.print(
                "─" * 70
            )

            console.print(content)

            console.print(
                "─" * 70
            )


        # ----------------------------------------------------
        # Normal response
        # ----------------------------------------------------

        else:

            message = result.get(
                "message",
                "Directive accomplished."
            )

            jarvis_hud.print_jarvis_response(
                message,
                title=BUTLER_NAME
            )


        # ====================================================
        # VOICE OUTPUT
        # ====================================================

        spoken = (
            result.get("speak")
            or result.get("message")
        )

        if spoken and is_voice_enabled():

            speak(spoken)


    # ========================================================
    # FAILURE
    # ========================================================

    else:

        error_message = result.get(
            "error",
            "An unexpected protocol failure occurred."
        )

        console.print(
            f"\n[bold red]⚠️ "
            f"{BUTLER_NAME} > "
            f"{error_message}[/bold red]\n"
        )

        if is_voice_enabled():

            speak(
                f"Forgive me {USER_TITLE}, "
                f"{error_message}"
            )


    return True


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            f"{BUTLER_NAME} "
            "AI Desktop Assistant"
        )
    )

    parser.add_argument(
        "--voice",
        action="store_true",
        help=(
            "Start directly in continuous "
            "voice listening mode"
        )
    )

    parser.add_argument(
        "--mute",
        action="store_true",
        help=(
            "Start with speech synthesis muted"
        )
    )

    args = parser.parse_args()


    # ========================================================
    # SYSTEM INITIALIZATION
    # ========================================================

    try:

        initialize()

    except Exception as error:

        console.print(
            "[bold red]⚠️ "
            "Tool system initialization failed:"
            "[/bold red]"
        )

        console.print(
            f"[red]{error}[/red]"
        )

        return


    # ========================================================
    # CHECK OLLAMA / NEURAL CORE
    # ========================================================

    try:

        core_ok, active_model = (
            ai_interpreter.ensure_neural_core()
        )

    except AttributeError:

        # ----------------------------------------------------
        # Compatibility fallback
        #
        # If ensure_neural_core() has not been implemented
        # yet, Astra will still start and use OLLAMA_MODEL.
        # ----------------------------------------------------

        core_ok = True
        active_model = OLLAMA_MODEL

    except Exception as error:

        core_ok = False
        active_model = OLLAMA_MODEL

        console.print(
            "[bold yellow]⚠️ "
            f"Neural core check failed: {error}"
            "[/bold yellow]"
        )


    if core_ok:

        model_display = active_model

    else:

        model_display = (
            f"{active_model} "
            "(Connecting)"
        )


    # ========================================================
    # INITIAL VOICE STATE
    # ========================================================

    if args.mute:

        execute({
            "action": "set_voice",
            "enabled": False
        })


    # ========================================================
    # HUD
    # ========================================================

    console.clear()

    jarvis_hud.print_banner(
        model_name=model_display,
        voice_enabled=is_voice_enabled()
    )


    # ========================================================
    # STARTUP GREETING
    # ========================================================

    welcome_text = (
        f"Jarvis initialized and ready "
        f"for your command, {USER_TITLE}."
    )

    console.print(
        f"[bold cyan]✦ {BUTLER_NAME}:[/bold cyan] "
        f"[italic bright_white]"
        f"{welcome_text}"
        f"[/italic bright_white]"
    )

    console.print(
        "[dim cyan]"
        "Type 'help' for capabilities, "
        "'listen' for voice input, "
        "or 'exit' to shut down."
        "[/dim cyan]\n"
    )

    if is_voice_enabled():

        speak(welcome_text)


    # ========================================================
    # CONTINUOUS VOICE MODE
    # ========================================================

    if args.voice:

        console.print(
            "[bold green]"
            "Continuous voice listening mode active. "
            "Press Ctrl+C to switch to text mode."
            "[/bold green]\n"
        )

        while True:

            try:

                spoken_cmd = (
                    handle_voice_listen_mode()
                )

                if spoken_cmd:

                    keep_running = (
                        run_command_cycle(
                            spoken_cmd
                        )
                    )

                    if not keep_running:
                        break

                time.sleep(0.5)

            except KeyboardInterrupt:

                console.print(
                    "\n[yellow]"
                    "Switched to manual console input mode."
                    "[/yellow]\n"
                )

                break


    # ========================================================
    # STANDARD INTERACTIVE REPL
    # ========================================================

    while True:

        try:

            prompt_voice_badge = (
                "[green]🔊[/green]"
                if is_voice_enabled()
                else "[dim]🔇[/dim]"
            )

            cmd = console.input(
                "[bold cyan]JARVIS[/bold cyan] "
                f"{prompt_voice_badge} "
                "[bold bright_white]You > [/bold bright_white]"
            ).strip()

        except KeyboardInterrupt:

            farewell = (
                f"Farewell, {USER_TITLE}."
            )

            console.print(
                f"\n\n"
                f"[bold cyan]"
                f"{BUTLER_NAME} > "
                f"{farewell}"
                f"[/bold cyan]"
            )

            if is_voice_enabled():

                speak(
                    farewell,
                    wait=True
                )

            break

        except EOFError:

            break


        if not cmd:

            continue


        # ====================================================
        # MICROPHONE SHORTCUT
        # ====================================================

        if cmd.lower() in [
            "listen",
            "voice",
            "mic",
            "talk",
            "hear me",
        ]:

            spoken_cmd = (
                handle_voice_listen_mode()
            )

            if spoken_cmd:

                keep_running = (
                    run_command_cycle(
                        spoken_cmd
                    )
                )

                if not keep_running:

                    break

            continue


        # ====================================================
        # NORMAL COMMAND
        # ====================================================

        keep_running = (
            run_command_cycle(cmd)
        )

        if not keep_running:

            break


# ============================================================
# PROGRAM ENTRY
# ============================================================

if __name__ == "__main__":
    main()