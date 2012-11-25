#!/usr/bin/perl

use strict;
use warnings;

my @dependencies;
my %checked;

for(@ARGV){
	$checked{$_} = 1;
	#push @dependencies, $_;
}

while(<>){
	s/(^|[^\\])%.*$/$1/;

	s(\\includegraphics(\[[^\]]*\])?\{([^}]*)\})(
#		my $fn = "$dir$2";
		my $fn = $2;
		if(!defined($checked{$fn})){
			push @dependencies, $fn;
			$checked{$fn} = 1;
		}
	)e;

	s(\\addbibresource\{([^}]*)\})(
		my $fn = $1;
		if(!defined($checked{$fn})){
			push @dependencies, $fn;
			$checked{$fn} = 1;
		}
	)e;

	s(\\input\{([^}]*)\})(
#		my $fn = "$dir$1.tex";
		my $fn = $1;
		$fn .= ".tex" unless $fn =~ /\.pdf_tex$/;
		if(!defined($checked{$fn})){
			push @dependencies, $fn;
			push @ARGV, $fn unless $fn =~ /\.pdf_tex$/;
			$checked{$fn} = 1;
		}
	)e;

	s(\\usepackage\{([^}]*)\})(
		my $fn = "$1.sty";
		if(-f $fn && !defined($checked{$fn})){
			push @dependencies, $fn;
			push @ARGV, $fn;
			$checked{$fn} = 1;
		}
	)e;

}

print join " ", @dependencies;
print "\n";
