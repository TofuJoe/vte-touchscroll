// C twin of min.py: VteTerminal in a GtkScrolledWindow, nothing else.
#include <gtk/gtk.h>
#include <vte/vte.h>

static void
on_value_changed(GtkAdjustment *adj, gpointer data)
{
        g_print("[scroll] %.1f\n", gtk_adjustment_get_value(adj));
}

static gboolean
quit_cb(gpointer app)
{
        g_application_quit(G_APPLICATION(app));
        return G_SOURCE_REMOVE;
}

static void
activate(GtkApplication *app, gpointer data)
{
        GtkWidget *win = gtk_application_window_new(app);
        gtk_window_set_default_size(GTK_WINDOW(win), 1000, 800);

        GtkWidget *term = vte_terminal_new();
        vte_terminal_set_scrollback_lines(VTE_TERMINAL(term), 10000);

        GtkWidget *sw = gtk_scrolled_window_new();
        gtk_scrolled_window_set_policy(GTK_SCROLLED_WINDOW(sw),
                                       GTK_POLICY_NEVER, GTK_POLICY_ALWAYS);
        gtk_scrolled_window_set_child(GTK_SCROLLED_WINDOW(sw), term);
        gtk_window_set_child(GTK_WINDOW(win), sw);

        GString *blob = g_string_new(NULL);
        for (int i = 1; i <= 400; i++)
                g_string_append_printf(blob, "line %04d %s\r\n", i,
                                       "............................................................");
        vte_terminal_feed(VTE_TERMINAL(term), blob->str, blob->len);
        g_string_free(blob, TRUE);

        g_signal_connect(gtk_scrollable_get_vadjustment(GTK_SCROLLABLE(term)),
                         "value-changed", G_CALLBACK(on_value_changed), NULL);

        gtk_window_present(GTK_WINDOW(win));
        g_print("[ready]\n");
        g_timeout_add(40000, quit_cb, app);
}

int
main(int argc, char **argv)
{
        GtkApplication *app = gtk_application_new("test.MinC", G_APPLICATION_NON_UNIQUE);
        g_signal_connect(app, "activate", G_CALLBACK(activate), NULL);
        return g_application_run(G_APPLICATION(app), 0, NULL);
}
