\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{stand}[2025/04/04 ORT standalone multi + border]

% Передаём все неизвестные опции сразу в standalone
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{standalone}}
\ProcessOptions\relax

% Загрузка standalone с нужными опциями
%\LoadClass[border=5mm,varwidth=127mm, multi=page, crop]{standalone}
\LoadClass[border=5mm,varwidth=90mm, multi=page, crop]{standalone}

% Остальные пакеты, как в вашем ort.cls
\RequirePackage[OT2, T2A, T1]{fontenc}
\RequirePackage[russian]{babel}
\RequirePackage{amsmath, amssymb, graphicx, array, multicol, tikz, pgfplots, mathrsfs, colortbl, array, tikz-3dplot, pgf-pie}
\pgfplotsset{compat=1.18}
\usepgfplotslibrary{polar}
\usetikzlibrary{angles,quotes,babel, patterns, calc}
\RequirePackage[shortlabels]{enumitem}
\RequirePackage{xcolor}
\RequirePackage{etoolbox} % Для счётчика
\RequirePackage[modulo]{lineno}
\renewcommand{\linenumberfont}{\normalfont\bfseries\small}

% Опция для включения/выключения нумерации
\newbool{shownumbering}
\newcommand{\shownumbering}{\booltrue{shownumbering}}
\newcommand{\hidenumbering}{\boolfalse{shownumbering}}

% По умолчанию нумерация выключена
\hidenumbering

% Цвета
\definecolor{graybar}{RGB}{210, 211, 212}
\definecolor{blackbar}{RGB}{30, 28, 29}

\newcommand{\noimg}{
  \begin{tikzpicture}
    \node[rotate=45,text width=7cm,text centered] at (0,0) {\Large ЗДЕСЬ ДОЛЖЕН БЫТЬ РИСУНОК};
  \end{tikzpicture}
}

% Счётчик
\newcounter{comparisoncounter}

% Макрос метки с заливкой
\newcommand{\comparisonlabel}{%
  \stepcounter{comparisoncounter}%
  \noindent
  \begin{tikzpicture}
    \def\barheight{0.5cm}
    \def\blackwidth{1cm}
    \fill[graybar] (0,0) rectangle (\textwidth,\barheight);
    \fill[blackbar] (0,0) rectangle (\blackwidth,\barheight);
    \node[text=white, font=\large] at ({\blackwidth/2}, {\barheight/2}) {\thecomparisoncounter};
    %\vspace{0.2cm}%
  \end{tikzpicture}
}

% Условный макрос для отображения метки
\newcommand{\conditionalcomparisonlabel}{%
  \ifbool{shownumbering}{\raggedright\comparisonlabel}{}%
}

% Две колонки
\newcommand{\comparisonbox}[3][1cm]{%
  \framebox{%
    \begin{minipage}{0.418\linewidth}
      \parbox[c][#1][c]{\linewidth}{\centering #2}%
    \end{minipage}%
  }%
  \begin{minipage}{0.100\linewidth}
    ~
  \end{minipage}
  \framebox{%
    \begin{minipage}{0.418\linewidth}
      \parbox[c][#1][c]{\linewidth}{\centering #3}%
    \end{minipage}%
  }%
}

% Макрос comparisonBIG
\newcommand{\comparisonBIG}[3][]{%
\begin{page}
  \begin{minipage}{\textwidth}%
    \begin{minipage}{\textwidth}
      \conditionalcomparisonlabel
      
      \if\relax\detokenize{#1}\relax%
        \vspace{0.35cm}
      \else
        \vspace{0.3cm}
        \centering #1%
        \vspace{0.4cm}
      \fi
      %\vspace{0.2cm}%
    \end{minipage}
    \begin{minipage}{\textwidth}%
      %\vspace{0.2cm}
      \comparisonbox[2cm]{#2}{#3}%
    \end{minipage}%
    %\vspace{4cm}%
  \end{minipage}%
\end{page}
}

% Макрос comparison
\newcommand{\comparison}[4][]{%
  \begin{page}
    \if\relax\detokenize{#4}\relax%
        \else
          %\vspace{0.3cm}
          \centering #4%
          \vspace{0.4cm}
        \fi
    \begin{minipage}{\textwidth}%
      \begin{minipage}{\textwidth}
        \conditionalcomparisonlabel
        
        \if\relax\detokenize{#1}\relax%
          \vspace{0.35cm}
        \else
          \vspace{0.3cm}
          \centering #1%
          \vspace{0.4cm}
        \fi
        %\vspace{0.2cm}%
      \end{minipage}
      \begin{minipage}{\textwidth}%
        %\vspace{0.2cm}
        \comparisonbox{#2}{#3}%
      \end{minipage}%
      %\vspace{4cm}%
    \end{minipage}%
  \end{page}
}

% Макрос ABCDE
\newcommand{\ABCDE}[7][]{%
  \begin{page}
    \if\relax\detokenize{#7}\relax%
        \else
          %\vspace{0.3cm}
          \centering #7%
          \vspace{0.4cm}
        \fi
    \begin{minipage}{\textwidth}%
      \conditionalcomparisonlabel
      \begin{minipage}{\textwidth}
        \vspace{0.3cm}
        #1%
        \vspace{0.35cm}
      %\end{minipage}
      %\begin{minipage}{\textwidth}
      \begin{enumerate}[itemsep=0cm, topsep=0cm, ]
        \item[(А)] #2
        \item[(Б)] #3
        \item[(В)] #4
        \item[(Г)] #5
        \item[(Д)] #6
      \end{enumerate}
    \end{minipage}
    %\vspace{4cm}%
    \end{minipage}%
    
  \end{page}
}

% Макрос question
\newcommand{\question}[5][]{%
  \begin{minipage}{\textwidth}%
    \conditionalcomparisonlabel
    #1
    \begin{enumerate}
      \item[А.] #2
      \item[Б.] #3
      \item[В.] #4
      \item[Г.] #5
    \end{enumerate}
  \end{minipage}%
}

% Текст с нумерацией строк
\newcommand{\textwr}[2]{%
  \vspace{0.2cm}%
  \begin{center}\textit{#1}\end{center}%
  \vspace{0.2cm}%
  \resetlinenumber%
  \begin{linenumbers}%
    #2%
  \end{linenumbers}%
  \vspace{0.2cm}%
}

\newcommand{\textnr}[2]{%
  \vspace{0.2cm}%
  \begin{center}\textit{#1}\end{center}%
  \vspace{0.2cm}%
  \begin{linenumbers}%
    #2%
  \end{linenumbers}%
  \vspace{0.2cm}%
}

\newcommand{\ld}{\underline{\hspace{1cm}}}

\endinput