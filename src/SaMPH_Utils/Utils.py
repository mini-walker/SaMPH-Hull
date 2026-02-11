#***********************************************************************
# Very important: you need to use usr_dir when you want to save data
# utils.resource_path only used for reading static files
#***********************************************************************

import sys
import re
import io
import base64
from pathlib import Path

# Try to import rendering libraries with detailed error logging
import logging
import traceback
import os

# Configure logging - try multiple locations for EXE compatibility
log_file = None
log_handlers = []

# Try to set up file logging
for log_path in [
    Path.cwd() / "usr/latex_rendering.log",  # Current working directory (works in EXE)
    Path(__file__).parent.parent.parent / "usr/latex_rendering.log" if not getattr(sys, 'frozen', False) else None,  # Dev mode
]:
    if log_path:
        try:
            # Ensure parent directory exists
            log_path.parent.mkdir(parents=True, exist_ok=True)
            # Test if we can write to this location
            with open(log_path, 'a') as test:
                test.write("")
            log_file = log_path
            log_handlers.append(logging.FileHandler(str(log_file), encoding='utf-8'))
            break
        except:
            pass

# Always add console handler as fallback
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
log_handlers.append(console_handler)

# Configure logging with handlers
logging.basicConfig(
    level=logging.WARNING,  # Only log warnings and errors (not DEBUG/INFO)
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)

# Log critical startup info only
if not getattr(sys, 'frozen', False):  # Only log in dev mode
    logging.info("="*60)
    logging.info("LaTeX Rendering Module Initialization")
    logging.info("="*60)
    logging.info(f"Log file: {log_file if log_file else 'Console only'}")
    logging.info(f"Python frozen (EXE): {getattr(sys, 'frozen', False)}")
    logging.info(f"Current working directory: {os.getcwd()}")

try:
    import matplotlib
    import matplotlib.pyplot as plt
    import latex2mathml.converter
    RENDERING_AVAILABLE = True
    
    # Configure matplotlib for headless rendering
    matplotlib.use('Agg')
    plt.rcParams['mathtext.fontset'] = 'cm'
    
except ImportError as e:
    RENDERING_AVAILABLE = False
    error_msg = f"Failed to import rendering libraries: {e}"
    print(f"[WARN] {error_msg}")
    logging.error(error_msg)
    logging.error(traceback.format_exc())
except Exception as e:
    RENDERING_AVAILABLE = False
    error_msg = f"Unexpected error during rendering library setup: {e}"
    print(f"[ERROR] {error_msg}")
    logging.error(error_msg)
    logging.error(traceback.format_exc())


class utils:

    #--------------------------------------------------------------
    # For local static files (relative to SaMPH package directory)
    @staticmethod
    def local_resource_path(relative_path):
        
        """
        Return an absolute resource path for SaMPH package resources.
        Base path: .../src/SaMPH/
        
        Example: local_resource_path("SaMPH_Utils/config.json") 
                 -> .../src/SaMPH/SaMPH_Utils/config.json
        """

        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = Path(sys._MEIPASS) / "SaMPH"
        except AttributeError:
            # __file__ is .../src/SaMPH/SaMPH_Utils/Utils.py
            # parent -> .../src/SaMPH/SaMPH_Utils
            # parent -> .../src/SaMPH
            base_path = Path(__file__).parent.parent.resolve()
        
        # Join with relative path and return as string
        return str(base_path / relative_path)
    #--------------------------------------------------------------


    #--------------------------------------------------------------
    # For global static files (relative to src directory)
    @staticmethod
    def global_resource_path(relative_path):
        
        """
        Return an absolute resource path for global project resources.
        Base path: .../src/
        
        Example: global_resource_path("images/logo.png") 
                 -> .../src/images/logo.png
        """

        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = Path(sys._MEIPASS)
        except AttributeError:
            # __file__ is .../src/SaMPH/SaMPH_Utils/Utils.py
            # parent -> .../src/SaMPH/SaMPH_Utils
            # parent -> .../src/SaMPH
            # parent -> .../src
            # parent -> .../SaMPH_V1 (project root)
            base_path = Path(__file__).parent.parent.parent.parent.resolve()
        
        # Join with relative path and return as string
        return str(base_path / relative_path)
    #--------------------------------------------------------------




    #--------------------------------------------------------------
    # For local dynamic files (SaMPH package user data)
    @staticmethod
    def get_local_usr_dir():
        """
        Get the user data directory for SaMPH package.
        Base path: .../usr/SaMPH/UserData/ (at project root level)
        """
        if getattr(sys, 'frozen', False):
            # The pyinstaller model
            base_dir = Path(sys.executable).parent
        else:
            # debug mode
            # Project Root
            base_dir = Path(__file__).resolve().parent.parent.parent.parent

        usr_dir = base_dir / "src" / "SaMPH" / "SaMPH_Usr"
        usr_dir.mkdir(parents=True, exist_ok=True)
        return usr_dir
    #--------------------------------------------------------------


    #--------------------------------------------------------------
    # For global dynamic files (project-wide user data)
    @staticmethod
    def get_global_usr_dir():
        """
        Get the global user data directory for the entire project.
        Base path: .../usr/ (at project root level)
        Fallback: %APPDATA%/SaMPH-Hull/usr if local dir is not writable
        """
        if getattr(sys, 'frozen', False):
            # The pyinstaller model
            base_dir = Path(sys.executable).parent
        else:
            # debug mode
            base_dir = Path(__file__).resolve().parent.parent.parent

        usr_dir = base_dir / "usr" / "SaMPH-Hull"
        
        # Check if we can write to this directory
        try:
            usr_dir.mkdir(parents=True, exist_ok=True)
            # Try creating a temp file to verify write permissions
            test_file = usr_dir / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
            except (PermissionError, OSError):
                # Fallback to APPDATA if local dir is read-only
                import os
                app_data = Path(os.getenv('APPDATA'))
                usr_dir = app_data / "SaMPH-Hull" / "usr"
                usr_dir.mkdir(parents=True, exist_ok=True)
                print(f"[INFO] Local dir read-only, using APPDATA: {usr_dir}")
        except Exception as e:
            print(f"[WARN] Failed to create/access usr dir: {e}")
            # Fallback to APPDATA
            import os
            app_data = Path(os.getenv('APPDATA'))
            usr_dir = app_data / "SaMPH-Hull" / "usr"
            usr_dir.mkdir(parents=True, exist_ok=True)

        return usr_dir
    #--------------------------------------------------------------

    #--------------------------------------------------------------
    # For Results directory
    @staticmethod
    def get_results_dir():
        """
        Get the results directory.
        Base path: .../usr/SaMPH-Hull/Results/ (at project root level)
        """
        results_dir = utils.get_global_usr_dir() / "Results"
        results_dir.mkdir(parents=True, exist_ok=True)
        return results_dir
    #--------------------------------------------------------------

    #--------------------------------------------------------------
    @staticmethod
    def convert_sub_and_superscript(text):
        """
        Convert unit text with ^ (superscript) and _ (subscript) to HTML format.

        Args:
            unit_text (str): The unit text (e.g., "m^2" or "m_3").

        Returns:
            str: HTML-formatted unit (e.g., "m<sup>2</sup>" or "m<sub>3</sub>").
        """

        # Transfer the unicode
        def replace_unicode(match):
            code = match.group(1)
            return chr(int(code, 16))
        
        text = re.sub(r'\\u([0-9A-Fa-f]{4})', replace_unicode, text)


        text = re.sub(r'_([^_}]+)', r'<sub>\1</sub>', text)
        text = re.sub(r'\^([^_^}]+)', r'<sup>\1</sup>', text)
        
        return text
    #--------------------------------------------------------------



    #--------------------------------------------------------------
    @staticmethod
    def convert_sub_and_superscript(text):
        """
        Convert unit text with ^ (superscript) and _ (subscript) to HTML format.

        Args:
            unit_text (str): The unit text (e.g., "m^2" or "m_3").

        Returns:
            str: HTML-formatted unit (e.g., "m<sup>2</sup>" or "m<sub>3</sub>").
        """
        # Transfer the unicode
        def replace_unicode(match):
            code = match.group(1)
            return chr(int(code, 16))
        
        text = re.sub(r'\\u([0-9A-Fa-f]{4})', replace_unicode, text)
        text = re.sub(r'_([^_}]+)', r'<sub>\1</sub>', text)
        text = re.sub(r'\^([^_^}]+)', r'<sup>\1</sup>', text)
        return text
    #--------------------------------------------------------------

    #--------------------------------------------------------------
    @staticmethod
    def sanitize_filename(name: str) -> str:
        """
        Replace invalid characters for Windows file names with '_'.
        """
        return re.sub(r'[<>:"/\\|?*]', "_", name)
    #--------------------------------------------------------------

    #--------------------------------------------------------------
    @staticmethod
    def build_chat_file_path(folder_name: str, chat_title: str, root_dir=None) -> Path:
        """
        Build a valid JSON file path for a chat under the given folder.

        Args:
            folder_name (str): Folder name.
            chat_title (str): Chat title (will be sanitized).
            root_dir (str|Path, optional): Root directory to store chat folders.
                If None, uses `.../usr/SaMPH/ChatHistory`.

        Returns:
            Path: Full path to chat JSON file.
        """
        if root_dir:
            base_path = Path(root_dir)
        else:
            base_path = utils.get_global_usr_dir() / "ChatHistory"

        folder_path = base_path / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)

        safe_title = utils.sanitize_filename(chat_title)
        return folder_path / f"{safe_title}.json"

    #--------------------------------------------------------------



    # ================================================================
    # SECTION: LaTeX and Math Rendering Utilities
    # ================================================================

    #--------------------------------------------------------------
    # Unicode to LaTeX Converter
    #--------------------------------------------------------------
    @staticmethod
    def unicode_to_latex(text):
        """
        Convert Unicode math symbols to LaTeX commands.
        
        This ensures matplotlib and latex2mathml can properly render 
        mathematical notation.
        
        Args:
            text (str): Input text with Unicode symbols
            
        Returns:
            str: Text with LaTeX commands
        """
        replacements = {
            # Greek letters (lowercase)
            'α': r'\alpha', 'β': r'\beta', 'γ': r'\gamma', 
            'δ': r'\delta', 'ε': r'\epsilon', 'ζ': r'\zeta', 
            'η': r'\eta', 'θ': r'\theta', 'ι': r'\iota', 
            'κ': r'\kappa', 'λ': r'\lambda', 'μ': r'\mu',
            'ν': r'\nu', 'ξ': r'\xi', 'ο': r'o', 'π': r'\pi',
            'ρ': r'\rho', 'ς': r'\varsigma', 'σ': r'\sigma', 
            'τ': r'\tau', 'υ': r'\upsilon', 'φ': r'\phi', 
            'χ': r'\chi', 'ψ': r'\psi', 'ω': r'\omega',
            
            # Greek letters (uppercase)
            'Α': r'A', 'Β': r'B', 'Γ': r'\Gamma', 'Δ': r'\Delta',
            'Ε': r'E', 'Ζ': r'Z', 'Η': r'H', 'Θ': r'\Theta',
            'Ι': r'I', 'Κ': r'K', 'Λ': r'\Lambda', 'Μ': r'M',
            'Ν': r'N', 'Ξ': r'\Xi', 'Ο': r'O', 'Π': r'\Pi',
            'Ρ': r'P', 'Σ': r'\Sigma', 'Τ': r'T', 
            'Υ': r'\Upsilon', 'Φ': r'\Phi', 'Χ': r'X', 
            'Ψ': r'\Psi', 'Ω': r'\Omega',
            
            # Math operators
            '±': r'\pm', '∓': r'\mp', '×': r'\times', '÷': r'\div',
            '≠': r'\neq', '≈': r'\approx', '≡': r'\equiv',
            '≤': r'\leq', '≥': r'\geq', '≪': r'\ll', '≫': r'\gg',
            '∞': r'\infty', '∂': r'\partial', '∇': r'\nabla',
            '∫': r'\int', '∮': r'\oint', '∑': r'\sum', '∏': r'\prod',
            '√': r'\sqrt', '∛': r'\sqrt[3]', '∜': r'\sqrt[4]',
            '∈': r'\in', '∉': r'\notin', '∋': r'\ni', 
            '∌': r'\not\ni', '⊂': r'\subset', '⊃': r'\supset', 
            '⊆': r'\subseteq', '⊇': r'\supseteq',
            '∪': r'\cup', '∩': r'\cap', '∅': r'\emptyset',
            '∀': r'\forall', '∃': r'\exists', '∄': r'\nexists',
            '∧': r'\wedge', '∨': r'\vee', '¬': r'\neg',
            '⇒': r'\Rightarrow', '⇐': r'\Leftarrow', 
            '⇔': r'\Leftrightarrow', '→': r'\rightarrow', 
            '←': r'\leftarrow', '↔': r'\leftrightarrow',
            '℘': r'\wp', 'ℜ': r'\Re', 'ℑ': r'\Im', 'ℵ': r'\aleph',
            '∝': r'\propto', '∠': r'\angle', '⊥': r'\perp', 
            '∥': r'\parallel',
            
            # Superscripts
            '⁰': r'^0', '¹': r'^1', '²': r'^2', '³': r'^3', 
            '⁴': r'^4', '⁵': r'^5', '⁶': r'^6', '⁷': r'^7', 
            '⁸': r'^8', '⁹': r'^9',
            
            # Subscripts
            '₀': r'_0', '₁': r'_1', '₂': r'_2', '₃': r'_3', 
            '₄': r'_4', '₅': r'_5', '₆': r'_6', '₇': r'_7', 
            '₈': r'_8', '₉': r'_9',
            
            # Special
            '°': r'^\circ',
        }
        
        for unicode_char, latex_cmd in replacements.items():
            text = text.replace(unicode_char, latex_cmd)
        
        return text
    #--------------------------------------------------------------

    #--------------------------------------------------------------
    # LaTeX to Base64 Image
    #--------------------------------------------------------------
    @staticmethod
    def latex_to_base64_block(
        latex_str, 
        font_size=12, 
        dpi=110, 
        max_width_px=800, 
        inline=False
    ):
        """
        Render LaTeX to Base64-encoded PNG image.
        
        Args:
            latex_str (str): LaTeX code
            font_size (int): Font size
            dpi (int): Resolution
            max_width_px (int): Maximum width in pixels
            inline (bool): True for inline formulas, False for block
            
        Returns:
            str: HTML img tag with Base64 image
        """
        if not RENDERING_AVAILABLE:
            logging.warning(f"LaTeX rendering unavailable for: {latex_str}")
            return "[LaTeX rendering unavailable]"
            
        clean_latex = f"${latex_str}$"
        safe_width_px = max(max_width_px, 100)
        
        try:
            # Measure text size
            temp_fig = plt.figure(figsize=(10, 1), dpi=dpi)
            temp_ax = temp_fig.add_axes([0, 0, 1, 1])
            temp_ax.set_axis_off()
            temp_text = temp_ax.text(
                0, 0, clean_latex, 
                fontsize=font_size, 
                color='black'
            )
            
            try:
                temp_fig.canvas.draw()
                bbox = temp_text.get_window_extent(
                    temp_fig.canvas.get_renderer()
                )
                w_in, h_in = bbox.width / dpi, bbox.height / dpi
            except Exception as e:
                logging.error(f"Failed to measure LaTeX bounds for '{latex_str}': {e}")
                logging.error(traceback.format_exc())
                w_in, h_in = 4, 0.5
            finally:
                plt.close(temp_fig)

            final_w = max(min(w_in, safe_width_px / dpi), 0.1)
            final_h = max(h_in, 0.1)
            
            # Render final image
            fig = plt.figure(figsize=(final_w, final_h), dpi=dpi)
            fig.text(
                0.5, 0.5, clean_latex, 
                fontsize=font_size, 
                color='black', 
                ha='center', 
                va='center'
            )
            
            buf = io.BytesIO()
            fig.savefig(
                buf, 
                format='png', 
                dpi=dpi, 
                transparent=True, 
                bbox_inches='tight', 
                pad_inches=0.02
            )
            plt.close(fig)
            buf.seek(0)
            img = base64.b64encode(buf.read()).decode('utf-8')
            
            # Return appropriate HTML based on inline/block mode
            if inline:
                return (
                    f'<img src="data:image/png;base64,{img}" '
                    f'style="display: inline; '
                    f'vertical-align: middle; '
                    f'height: 1.1em; width: auto; '
                    f'margin: 0 2px;" />'
                )
            else:
                return (
                    f'<div style="text-align: center; '
                    f'margin: 8px 0;">'
                    f'<img src="data:image/png;base64,{img}" '
                    f'style="max-width: 100%; height: auto; '
                    f'vertical-align: middle;" /></div>'
                )
        except Exception as e:
            error_msg = f"Failed to render LaTeX '{latex_str}': {e}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            logging.error(f"LaTeX string: {latex_str}")
            logging.error(f"Frozen: {getattr(sys, 'frozen', False)}")
            try:
                plt.close('all')
            except:
                pass
            return "[Error]"
    #--------------------------------------------------------------

    #--------------------------------------------------------------
    # LaTeX to MathML
    #--------------------------------------------------------------
    @staticmethod
    def latex_to_mathml_inline(latex_str):
        """
        Convert LaTeX to MathML for inline rendering.
        
        Args:
            latex_str (str): LaTeX code
            
        Returns:
            str: MathML HTML or error message
        """
        if not RENDERING_AVAILABLE:
            logging.warning(f"MathML unavailable for: {latex_str}")
            return "[MathML unavailable]"
            
        try:
            result = latex2mathml.converter.convert(latex_str)
            return result
        except Exception as e:
            error_msg = f"Failed to convert LaTeX to MathML '{latex_str}': {e}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            logging.error(f"LaTeX string: {latex_str}")
            logging.error(f"Frozen: {getattr(sys, 'frozen', False)}")
            return "[Error]"
    #--------------------------------------------------------------

    #--------------------------------------------------------------
    # Wrap Code Blocks
    #--------------------------------------------------------------
    @staticmethod
    def wrap_code_with_table(html):
        """
        Wrap code blocks with table styling for Qt rendering.
        
        Args:
            html (str): HTML content with code blocks
            
        Returns:
            str: HTML with styled code blocks
        """
        table_start = (
            '<table width="100%" bgcolor="#f4f6f8" border="0" '
            'cellspacing="0" cellpadding="0" '
            'style="border-radius: 8px; margin: 10px 0; '
            'border: 1px solid #d0d7de; border-collapse: separate;">'
            '<tr><td style="padding: 12px; color: #24292f;">'
        )
        table_end = '</td></tr></table>'
        pattern = r'<div class="codehilite">(.*?)</div>'
        
        return re.sub(
            pattern, 
            lambda m: f"{table_start}{m.group(1)}{table_end}", 
            html, 
            flags=re.DOTALL
        )
    #--------------------------------------------------------------
